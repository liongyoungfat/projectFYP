<script setup lang="ts">
import SideBar from '@/components/SideBar.vue'
</script>


<template>
  <div class="app-container">
    <div class="side-bar">
        <SideBar />
    </div>
    <main class="content-area">
        <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  width: 100vw;
}
.side-bar {
  width: 250px;
  background-color: #2c3e50;
}
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #1e1e1e;
}
</style>

