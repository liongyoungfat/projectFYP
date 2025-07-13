<script setup lang="ts">
import SideBar from '@/components/SideBar.vue'
import TopBar from '@/components/TopBar.vue'
</script>

<template>
  <div class="layout-wrapper">
    <header class="top-bar">
      <TopBar />
    </header>
    <div class="main-body">
      <aside class="side-bar">
        <SideBar />
      </aside>
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Top bar */
.top-bar {
  height: 64px;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
  padding: 0 32px;
  z-index: 10;
}

/* Main body: Sidebar + Content */
.main-body {
  display: flex;
  flex: 1;
  width: 100%;
}

/* Sidebar */
.side-bar {
  width: 250px;
  background-color: #f8f9fc;
  border-right: 1px solid #ddd;
  max-height: screen;
}

/* Content area */
.content-area {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f7fa;
  min-height: calc(100vh - 64px);
}
</style>
