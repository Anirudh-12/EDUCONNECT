<template>
  <div class="min-h-screen bg-[#0E0E12] text-white flex flex-col">
    <!-- Top Bar -->
    <header class="border-b border-[#2B2B36] px-6 py-4 flex items-center justify-between bg-[#18181F]">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-[#6C47FF] flex items-center justify-center font-bold text-white text-lg">
          E
        </div>
        <div>
          <h1 class="font-bold text-lg leading-tight">EDUCONNECT</h1>
          <p class="text-xs text-[#9CA3AF]">Local School Server Admin</p>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
          ● Server Online (Offline LAN)
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 p-8 max-w-7xl mx-auto w-full">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-[#18181F] p-6 rounded-xl border border-[#2B2B36]">
          <h3 class="text-sm font-medium text-[#9CA3AF]">Registered Students</h3>
          <p class="text-3xl font-bold mt-2 text-white">50</p>
          <p class="text-xs text-emerald-400 mt-1">Capacity: 50 max (MVP)</p>
        </div>
        <div class="bg-[#18181F] p-6 rounded-xl border border-[#2B2B36]">
          <h3 class="text-sm font-medium text-[#9CA3AF]">Published Courses</h3>
          <p class="text-3xl font-bold mt-2 text-white">4</p>
          <p class="text-xs text-[#9CA3AF] mt-1">12 active lessons</p>
        </div>
        <div class="bg-[#18181F] p-6 rounded-xl border border-[#2B2B36]">
          <h3 class="text-sm font-medium text-[#9CA3AF]">Sync Queue Status</h3>
          <p class="text-3xl font-bold mt-2 text-[#6C47FF]">0 Pending</p>
          <p class="text-xs text-emerald-400 mt-1">All devices acknowledged</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// Admin baseline
</script>
