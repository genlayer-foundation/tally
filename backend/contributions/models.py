from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from utils.models import BaseModel
import decimal
import os
import uuid

def evidence_file_path(instance, filename):
    """Generate a unique file path for evidence files."""
    # Generate a unique path for each file based on user and timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if instance.contribution:
        user_id = instance.contribution.user.id
        folder_type = 'contribution'
        parent_id = instance.contribution.id
    elif instance.submitted_contribution:
        user_id = instance.submitted_contribution.user.id
        folder_type = 'submission'
        parent_id = instance.submitted_contribution.id
    else:
        user_id = 'unassigned'
        folder_type = 'unknown'
        parent_id = 'no_parent'
    
    # Use timestamp instead of instance.id since it's not available yet
    folder = f"evidence/{folder_type}/{user_id}/{parent_id}"
    # Add timestamp to filename to ensure uniqueness
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    return os.path.join(folder, filename)


class ContributionType(BaseModel):
    """
    Represents different types of contributions that participants can make.
    Examples: Node Runner, Uptime, Asimov, Blog Post, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    min_points = models.PositiveIntegerField(default=0, help_text="Minimum points allowed for this contribution type")
    max_points = models.PositiveIntegerField(default=100, help_text="Maximum points allowed for this contribution type")

    def __str__(self):
        return self.name
        
    def clean(self):
        """Validate the contribution type data."""
        super().clean()
        
        # Ensure max_points is greater than or equal to min_points
        if self.max_points < self.min_points:
            raise ValidationError("Maximum points must be greater than or equal to minimum points")


class Contribution(BaseModel):
    """
    Represents a specific contribution made by a user.
    Links user with a contribution type and records points.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='contributions'
    )
    contribution_type = models.ForeignKey(
        ContributionType, 
        on_delete=models.CASCADE, 
        related_name='contributions'
    )
    points = models.PositiveIntegerField(default=0)
    frozen_global_points = models.PositiveIntegerField(default=0)
    multiplier_at_creation = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    contribution_date = models.DateTimeField(null=True, blank=True, help_text="Date when the contribution was made. Defaults to creation time if not specified.")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.contribution_type} - {self.points} points"
    
    def clean(self):
        """
        Validate that there is an active multiplier for this contribution type,
        that the user is visible, and that the points are within the allowed range.
        """
        super().clean()
        
        # Import here to avoid circular imports
        from django.utils import timezone
        from leaderboard.models import GlobalLeaderboardMultiplier
        
        # Check if the user is visible
        if not self.user.visible:
            raise ValidationError(
                f"Cannot add contributions for user '{self.user.email}' as they are marked as not visible. "
                "Only visible users can have contributions."
            )
        
        # Set contribution_date to now if not provided
        if not self.contribution_date:
            self.contribution_date = timezone.now()
        
        # Validate points are within the allowed range for this contribution type
        if self.points < self.contribution_type.min_points or self.points > self.contribution_type.max_points:
            raise ValidationError(
                f"Points must be between {self.contribution_type.min_points} and {self.contribution_type.max_points} "
                f"for contribution type '{self.contribution_type}'."
            )
        
        try:
            # Check if there's an active multiplier for this contribution type on the contribution date
            # The method returns a tuple of (multiplier_obj, multiplier_value)
            _, multiplier_value = GlobalLeaderboardMultiplier.get_active_for_type(
                self.contribution_type, 
                at_date=self.contribution_date
            )
            self.multiplier_at_creation = multiplier_value
        except GlobalLeaderboardMultiplier.DoesNotExist as e:
            raise ValidationError(
                f"No active multiplier exists for contribution type '{self.contribution_type}' "
                f"on {self.contribution_date.strftime('%Y-%m-%d %H:%M')}. "
                "Please set a multiplier that covers this date before adding contributions."
            ) from e
    
    def save(self, *args, **kwargs):
        """
        Override save to validate and calculate frozen_global_points.
        """
        from django.utils import timezone
        
        # Set contribution_date if not set yet
        if not self.contribution_date:
            self.contribution_date = timezone.now()
            
        # Only run validation on new contributions
        if not self.pk:
            self.clean()
            
            # Calculate frozen_global_points
            try:
                if self.multiplier_at_creation:
                    self.frozen_global_points = round(self.points * float(self.multiplier_at_creation))
            except (decimal.InvalidOperation, TypeError, ValueError):
                # Handle corrupted data by resetting the multiplier
                self.multiplier_at_creation = 1.0
                self.frozen_global_points = self.points
                
        super().save(*args, **kwargs)


# Signal to validate multiplier_at_creation before save
@receiver(pre_save, sender=Contribution)
def validate_multiplier_at_creation(sender, instance, **kwargs):
    """
    Signal to validate multiplier_at_creation before saving a Contribution.
    This helps prevent corrupted decimal values.
    """
    if instance.multiplier_at_creation:
        try:
            # Test if we can convert the decimal value
            float(instance.multiplier_at_creation)
        except (decimal.InvalidOperation, TypeError, ValueError):
            # If conversion fails, reset the multiplier to 1.0
            print(f"WARNING: Fixing corrupted multiplier_at_creation value for contribution {instance.id}")
            instance.multiplier_at_creation = 1.0
            instance.frozen_global_points = instance.points


class SubmittedContribution(BaseModel):
    """
    Represents a contribution submission that needs staff review.
    Once accepted, it will be converted to an actual Contribution.
    """
    # Use UUID for public-facing URLs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_contributions'
    )
    contribution_type = models.ForeignKey(
        ContributionType,
        on_delete=models.CASCADE,
        related_name='submitted_contributions'
    )
    contribution_date = models.DateTimeField(
        help_text="Date when the contribution was made"
    )
    notes = models.TextField(blank=True)
    
    # State management
    STATE_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('more_info_needed', 'More Information Needed')
    ]
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='pending'
    )
    
    # Review fields
    staff_reply = models.TextField(
        blank=True,
        help_text="Response from staff member"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_submissions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Link to actual contribution when accepted
    converted_contribution = models.ForeignKey(
        'Contribution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_submission'
    )
    
    # Edit tracking
    last_edited_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user} - {self.contribution_type} - {self.state}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Submitted Contribution"
        verbose_name_plural = "Submitted Contributions"


class Evidence(BaseModel):
    """
    Represents evidence for a contribution or submitted contribution.
    Can be text, a URL, or a file upload.
    """
    # Nullable FKs to both models
    contribution = models.ForeignKey(
        'Contribution',
        on_delete=models.CASCADE,
        related_name='evidence_items',
        null=True,
        blank=True
    )
    submitted_contribution = models.ForeignKey(
        'SubmittedContribution',
        on_delete=models.CASCADE,
        related_name='evidence_items',
        null=True,
        blank=True
    )
    
    description = models.TextField(blank=True, help_text="Description of the evidence")
    url = models.URLField(blank=True, help_text="Link to external evidence")
    file = models.FileField(upload_to=evidence_file_path, blank=True, null=True, help_text="Upload file as evidence")
    
    def __str__(self):
        if self.contribution:
            return f"Evidence for {self.contribution}"
        elif self.submitted_contribution:
            return f"Evidence for submitted: {self.submitted_contribution}"
        return "Evidence (unlinked)"
    
    def clean(self):
        """Validate that at least one of description, url, or file is provided."""
        super().clean()
        
        # Validate that evidence belongs to exactly one parent
        if self.contribution and self.submitted_contribution:
            raise ValidationError("Evidence can only belong to either a contribution or a submitted contribution, not both.")
        if not self.contribution and not self.submitted_contribution:
            raise ValidationError("Evidence must belong to either a contribution or a submitted contribution.")
        
        # Validate that at least one evidence type is provided
        if not self.description and not self.url and not self.file:
            raise ValidationError("At least one of description, URL, or file must be provided for evidence.")
        
    class Meta:
        verbose_name = "Evidence"
        verbose_name_plural = "Evidence Items"
