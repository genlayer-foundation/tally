<script>
  import { onMount } from 'svelte';
  import { push, querystring } from 'svelte-spa-router';
  import { format } from 'date-fns';
  import ContributionsList from '../components/ContributionsList.svelte';
  import StatCard from '../components/StatCard.svelte';
  import ValidatorStatus from '../components/ValidatorStatus.svelte';
  import { usersAPI, statsAPI, leaderboardAPI } from '../lib/api';
  
  // Import route params from svelte-spa-router
  import { params } from 'svelte-spa-router';
  
  // State management
  let participant = $state(null);
  let contributionStats = $state({
    totalContributions: 0,
    totalPoints: 0,
    averagePoints: 0,
    contributionTypes: []
  });
  let isValidatorOnly = $state(false); // Track if this is just a validator without user account
  
  let loading = $state(true);
  let error = $state(null);
  let statsError = $state(null);
  
  $effect(() => {
    const currentParams = $params;
    console.log("ParticipantProfile params:", currentParams);
    
    if (currentParams && currentParams.address) {
      console.log("Using params.address:", currentParams.address);
      fetchParticipantData(currentParams.address);
    } else {
      console.log("No valid address found");
      error = "No valid wallet address provided";
      loading = false;
    }
  });
  
  async function fetchParticipantData(participantAddress) {
    try {
      loading = true;
      error = null;
      
      console.log("Fetching participant data for address:", participantAddress);
      
      // Fetch participant details
      const res = await usersAPI.getUserByAddress(participantAddress);
      console.log("Participant data received:", res.data);
      console.log("Leaderboard entry data:", res.data.leaderboard_entry);
      participant = res.data;
      
      // Also try to fetch the leaderboard entry directly
      try {
        const leaderboardRes = await leaderboardAPI.getLeaderboardEntry(participantAddress);
        console.log("Leaderboard data received:", leaderboardRes.data);
        
        // If the leaderboard entry isn't included in the user data, add it
        if (!participant.leaderboard_entry && leaderboardRes.data.results && leaderboardRes.data.results.length > 0) {
          participant.leaderboard_entry = leaderboardRes.data.results[0];
          console.log("Added leaderboard entry from separate request:", participant.leaderboard_entry);
        }
      } catch (leaderboardError) {
        console.warn('Leaderboard API error:', leaderboardError);
      }
      
      // Fetch participant stats
      try {
        const statsRes = await statsAPI.getUserStats(participantAddress);
        if (statsRes.data) {
          contributionStats = statsRes.data;
          console.log("Stats data received:", statsRes.data);
        }
      } catch (statsError) {
        console.warn('Stats API error, will use basic data:', statsError);
        statsError = statsError.message || 'Failed to load participant statistics';
      }
      
      loading = false;
    } catch (err) {
      // Check if it's a 404 (user not found) - for validators without accounts
      if (err.response && err.response.status === 404) {
        // Create a minimal participant object for validators without accounts
        participant = {
          address: participantAddress,
          name: null,
          leaderboard_entry: {
            total_points: 0,
            rank: null
          },
          created_at: null
        };
        isValidatorOnly = true;
        loading = false;
        error = null; // Clear the error since this is a valid state
      } else {
        error = err.message || 'Failed to load participant data';
        loading = false;
      }
    }
    
    // We've moved the contributions loading to the ContributionsList component
    // so we don't need to fetch them here anymore
  }
  
  function formatDate(dateString) {
    try {
      return format(new Date(dateString), 'MMM d, yyyy');
    } catch (e) {
      return dateString;
    }
  }
  
  // Icons for stat cards
  const icons = {
    contributions: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    points: 'M13 10V3L4 14h7v7l9-11h-7z',
    rank: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
  };
</script>

<div>
  <div class="mb-5">
    <a href="/" onclick={(e) => { e.preventDefault(); push('/'); }} class="text-primary-600 hover:text-primary-700">
      ← Back to Dashboard
    </a>
  </div>
  
  <!-- Connection error message if needed -->
  {#if error || statsError}
    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-yellow-700">
            Having trouble connecting to the API. Some data might not display correctly.
          </p>
        </div>
      </div>
    </div>
  {/if}
  
  {#if loading}
    <div class="flex justify-center items-center p-8">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
      {error}
    </div>
  {:else if participant}
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 flex items-center">
        {participant.name || (isValidatorOnly ? 'Validator' : 'Participant')} 
        {#if !isValidatorOnly && participant.visible !== false}
          <span class="ml-3 inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-primary-100 text-primary-800">
            Rank #{participant.leaderboard_entry?.rank || 'N/A'}
          </span>
        {/if}
      </h1>
      <p class="mt-1 text-sm text-gray-500">
        {#if isValidatorOnly}
          This validator has not created an account yet
        {:else if participant.visible === false}
          This participant is not currently listed on the leaderboard
        {:else}
          Wallet details and contributions
        {/if}
      </p>
    </div>
    
    <div class="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
      <div class="border-t border-gray-200">
        <dl>
          {#if participant.address}
            <div class="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt class="text-sm font-medium text-gray-500">
                Wallet Address
              </dt>
              <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                <div class="font-mono mb-2">{participant.address}</div>
                <ValidatorStatus address={participant.address} />
              </dd>
            </div>
          {/if}
          {#if !isValidatorOnly}
            <div class="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt class="text-sm font-medium text-gray-500">
                Total Points
              </dt>
              <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {participant.leaderboard_entry?.total_points || 0}
              </dd>
            </div>
            <div class="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt class="text-sm font-medium text-gray-500">
                Joined
              </dt>
              <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {formatDate(participant.created_at)}
              </dd>
            </div>
          {/if}
        </dl>
      </div>
    </div>
    
    {#if !isValidatorOnly}
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
        <StatCard 
          title="Total Contributions" 
          value={contributionStats.totalContributions || 0} 
          icon={icons.contributions}
          color="green"
        />
        <StatCard 
          title="Total Points" 
          value={participant.leaderboard_entry?.total_points || 0} 
          icon={icons.points}
          color="purple"
        />
        <StatCard 
          title="Current Rank" 
          value={participant.leaderboard_entry?.rank || 'N/A'} 
          icon={icons.rank}
          color="blue"
        />
      </div>
    {:else}
      <!-- Simple message for validators without accounts -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No Account Found</h3>
        <p class="mt-1 text-sm text-gray-500">This validator has not created an account yet.</p>
      </div>
    {/if}
    
    
    
    <!-- Contribution Types Breakdown -->
    {#if !isValidatorOnly && contributionStats.contributionTypes && contributionStats.contributionTypes.length > 0}
      <div class="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">
            Contribution Breakdown
          </h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">
            Points by contribution type
          </p>
        </div>
        <div class="border-t border-gray-200">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Count
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Points
                  </th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    % of Total
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                {#each contributionStats.contributionTypes as type, i}
                  <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <a 
                        href={`/contribution-type/${type.id}`}
                        onclick={(e) => { e.preventDefault(); push(`/contribution-type/${type.id}`); }}
                        class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 cursor-pointer hover:bg-green-200"
                      >
                        {type.name}
                      </a>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {type.count}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {type.total_points}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                          <div class="bg-primary-600 h-2.5 rounded-full" style={`width: ${type.percentage}%`}></div>
                        </div>
                        <span class="ml-2 text-sm text-gray-600">{type.percentage.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Contributions -->
    {#if !isValidatorOnly}
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4">{participant.name || 'Participant'}'s Contributions</h2>
        <ContributionsList
          userAddress={participant.address}
          showUser={false}
        />
      </div>
    {/if}
  {:else}
    <div class="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
      Participant not found
    </div>
  {/if}
</div>