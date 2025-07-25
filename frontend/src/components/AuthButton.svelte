<!-- AuthButton.svelte -->
<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { authState, signInWithEthereum, logout, verifyAuth } from '../lib/auth';
  
  // Use $: to access the store values reactively
  $: isAuthenticated = $authState.isAuthenticated;
  $: address = $authState.address;
  $: storeLoading = $authState.loading;
  $: storeError = $authState.error;
  
  let loading = false;
  let error = null;
  let showDropdown = false;
  let errorTimeout;
  
  // Auto-dismiss error messages after 5 seconds
  $: if (error || storeError) {
    if (errorTimeout) clearTimeout(errorTimeout);
    errorTimeout = setTimeout(() => {
      error = null;
      if (storeError) authState.setError(null);
    }, 5000);
  }
  
  onMount(async () => {
    try {
      await verifyAuth();
    } catch (err) {
      console.error('Auth verification error:', err);
    }
    
    return () => {
      if (errorTimeout) clearTimeout(errorTimeout);
    };
  });
  
  async function handleAuth() {
    if (isAuthenticated) {
      // If authenticated, clicking the button should toggle the dropdown
      showDropdown = !showDropdown;
      return;
    }
    
    // Otherwise, start the connection process
    loading = true;
    error = null;
    
    try {
      await signInWithEthereum();
    } catch (err) {
      console.error('Auth error:', err);
      // Create a curated error message
      if (err.message?.includes('MetaMask is not installed')) {
        error = 'Please install MetaMask to connect';
      } else if (err.message?.includes('User rejected') || err.message?.includes('User denied')) {
        error = 'Connection rejected';
      } else if (err.message?.includes('signature')) {
        error = 'Signature verification failed';
      } else if (err.message?.includes('nonce')) {
        error = 'Authentication expired, please try again';
      } else {
        error = 'Connection failed';
      }
    } finally {
      loading = false;
    }
  }
  
  async function handleLogout() {
    showDropdown = false;
    await logout();
  }
  
  function navigateToProfile() {
    if (address) {
      showDropdown = false;
      push(`/participant/${address}`);
    }
  }
  
  function formatAddress(addr) {
    if (!addr) return '';
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
  }
  
  function handleClickOutside(event) {
    if (showDropdown && !event.target.closest('.auth-dropdown-container')) {
      showDropdown = false;
    }
  }
  
  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<div class="auth-dropdown-container">
  <button 
    class="auth-button {isAuthenticated ? 'connected' : ''}" 
    on:click={handleAuth}
    disabled={loading || storeLoading}
    data-auth-button
  >
    {#if loading || storeLoading}
      <span class="loading-spinner"></span>
    {:else if isAuthenticated}
      <span class="address">{formatAddress(address)}</span>
      <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    {:else}
      <span>Connect Wallet</span>
    {/if}
  </button>
  
  {#if showDropdown && isAuthenticated}
    <div class="auth-dropdown">
      <div class="dropdown-address">
        {address}
      </div>
      <button class="dropdown-item" on:click={navigateToProfile}>
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
        </svg>
        View Profile
      </button>
      <button class="dropdown-item logout" on:click={handleLogout}>
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
        </svg>
        Disconnect
      </button>
    </div>
  {/if}
  
  {#if error || storeError}
    <div class="auth-error">
      {error || storeError}
    </div>
  {/if}
</div>

<style>
  .auth-dropdown-container {
    position: relative;
  }
  
  .auth-button {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: #2563eb;
    color: white;
    border: none;
    min-width: 140px;
  }
  
  .auth-button:hover {
    background-color: #1d4ed8;
  }
  
  .auth-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .auth-button.connected {
    background-color: #059669;
  }
  
  .auth-button.connected:hover {
    background-color: #047857;
  }
  
  .loading-spinner {
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .auth-dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    z-index: 50;
    min-width: 280px;
    background-color: white;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }
  
  .dropdown-address {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    color: #6b7280;
    border-bottom: 1px solid #e5e7eb;
    word-break: break-all;
    background-color: #f9fafb;
    font-family: monospace;
  }
  
  .dropdown-item {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.875rem;
    color: #374151;
    background-color: transparent;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .dropdown-item:hover {
    background-color: #f3f4f6;
  }
  
  .dropdown-item.logout {
    color: #ef4444;
  }
  
  .dropdown-item.logout:hover {
    background-color: #fef2f2;
  }
  
  .auth-error {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    padding: 0.75rem 1rem;
    background-color: #fee2e2;
    border: 1px solid #f87171;
    color: #b91c1c;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    z-index: 50;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    min-width: 200px;
    max-width: 300px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .auth-error::before {
    content: "⚠️";
    margin-right: 0.5rem;
  }
</style>