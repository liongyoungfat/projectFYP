<template>
  <div class="container">
    <!-- Sidebar -->
    <div class="sidebar">
      <h2 class="sidebar-title">Finance Dashboard</h2>
      <nav class="nav">
        <router-link to="/" class="nav-link" active-class="active">
          Dashboard
        </router-link>
        <router-link to="/expenses" class="nav-link" active-class="active">
          Expenses
        </router-link>
        <router-link to="/revenue" class="nav-link" active-class="active">
          Revenue
        </router-link>
      </nav>
    </div>
  </div>
</template>

<style lang="css" scoped>
.sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
  padding: 20px;
  position: fixed;
  height: 100%;
}

.sidebar-title {
  margin-bottom: 30px;
  font-size: 1.5rem;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.nav-link {
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px;
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-link:hover {
  background: #34495e;
}

.nav-link.active {
  background: #3498db;
}
</style>
