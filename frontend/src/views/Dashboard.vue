<template>
  <div>
    <BossDashboard v-if="role === 'boss'" />
    <ClerkDashboard v-else-if="role === 'clerk'" />
    <LeaderDashboard v-else />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BossDashboard from '../components/BossDashboard.vue'
import ClerkDashboard from '../components/ClerkDashboard.vue'
import LeaderDashboard from '../components/LeaderDashboard.vue'

const role = computed(() => localStorage.getItem('currentRole') || 'clerk')
</script>
