<script setup lang="ts"></script>

<template>
  <div>
    <router-view />
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  width: 100vw; /* Ensure full width */
}

.side-bar {
  width: 250px; /* or whatever fixed width you want */
  height: 100vh; /* Full height */
  background-color: #2c3e50; /* optional */
}

.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #1e1e1e; /* optional: make it match your design */
}
</style>
