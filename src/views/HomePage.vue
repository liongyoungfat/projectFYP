<template>
  <div class="homepage-font">
    <!-- Navigation Bar -->
    <nav class="navbar">
      <div class="navbar-left">
        <img src="/src/assets/logo.png" alt="Logo" class="logo-img" />
        <span class="brand">FinancePro</span>
      </div>
      <div class="navbar-right">
        <router-link to="/login" class="login-link">Login</router-link>
        <router-link to="/register" class="register-link">Get Started</router-link>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-overlay">
        <h1 class="hero-title">
          Professional Financial<br />
          Forecasting Platform
        </h1>
        <p class="hero-desc">
          Harness the power of AI-driven analytics to make informed financial decisions. Our
          platform provides accurate forecasting, real-time insights, and comprehensive reporting
          tools.
        </p>
        <div class="hero-btn-row">
          <router-link to="/register" class="hero-btn-blue">Start Free Trial</router-link>
          <router-link to="/login" class="hero-btn-blur">Sign In</router-link>
        </div>
      </div>
    </section>
    <!-- Why Choose Section -->
    <!-- Why Choose Section -->
    <section class="why-section">
      <div class="why-container">
        <h2 class="why-title">Why Choose FinancePro?</h2>
        <p class="why-subtitle">
          Built by financial experts for financial professionals. Experience the future of financial
          analysis.
        </p>
        <div class="why-features">
          <div class="why-card">
            <div class="why-icon">
              <img
                src="https://cdn-icons-png.flaticon.com/512/9296/9296582.png"
                alt="Forecasting Icon"
              />
            </div>
            <h3>Advanced Forecasting</h3>
            <p>AI-powered financial predictions with 95% accuracy rate</p>
          </div>
          <div class="why-card">
            <div class="why-icon">
              <img src="https://cdn-icons-png.flaticon.com/512/942/942748.png" alt="Team Icon" />
            </div>
            <h3>Financial Management and Staff Management</h3>
            <p>Comprehensive tools for managing finances and coordinating team operations</p>
          </div>
          <div class="why-card">
            <div class="why-icon">
              <img
                src="https://cdn-icons-png.flaticon.com/512/9714/9714561.png"
                alt="Dashboard Icon"
              />
            </div>
            <h3>Intuitive Dashboard</h3>
            <p>Clean, professional interface designed for financial professionals</p>
          </div>
          <div class="why-card">
            <div class="why-icon">
              <img src="https://cdn-icons-png.flaticon.com/512/3465/3465176.png" alt="Tax Icon" />
            </div>
            <h3>Tax Management</h3>
            <p>Simplify tax planning and compliance with automated tools</p>
          </div>
        </div>
      </div>
    </section>
    <!-- Real-time Analytics Section -->
    <section class="analytics-section">
      <div class="analytics-container">
        <div class="analytics-text">
          <h2>Real-time Financial Analytics</h2>
          <p>
            Monitor your portfolio performance, track market trends, and receive instant alerts on
            significant changes. Our advanced algorithms analyze thousands of data points to provide
            you with actionable insights.
          </p>
          <ul>
            <li>✅ Live market data integration</li>
            <li>✅ Customizable alert system</li>
            <li>✅ Advanced risk assessment</li>
            <li>✅ Portfolio optimization tools</li>
          </ul>
        </div>
        <div class="analytics-image">
          <img src="/src/assets/analytics-dashboard.jpg" alt="Analytics Dashboard" />
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <h2>Ready to Transform Your Financial Management?</h2>
      <p>
        Join thousands of professionals who trust FinancePro for their financial forecasting needs.
      </p>
      <router-link to="/register" class="cta-button">Get Started Today</router-link>
    </section>
    <!-- Footer -->
    <footer class="footer-section">
      <div class="footer-container">
        <!-- Left: Logo + Description -->
        <div class="footer-left">
          <div class="footer-brand">
            <img src="/src/assets/logo.png" alt="FinancePro Logo" class="footer-logo" />
            <h3 class="footer-title">FinancePro</h3>
          </div>
          <p class="footer-desc">
            Professional financial forecasting platform for modern businesses.
          </p>
        </div>

        <!-- Right: Contact Links -->
        <div class="footer-right">
          <p>
            📧
            <a href="mailto:liongyeong@gmail.com">Contact me via Email</a>
          </p>
          <p>
            🔗
            <a href="https://www.linkedin.com/in/liong-young-fat-200349267" target="_blank">
              LinkedIn Profile
            </a>
          </p>
        </div>
      </div>

      <div class="footer-bottom">&copy; 2024 FinancePro. All rights reserved.</div>
    </footer>
  </div>
</template>

<style scoped>
.homepage-font {
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 16px 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
}
.navbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-img {
  height: 60px;
  width: 60px;
  object-fit: contain;
}
.brand {
  font-weight: bold;
  font-size: 1.125rem;
  color: #1e293b;
}
.navbar-right {
  display: flex;
  align-items: center;
}
.login-link {
  color: #374151;
  font-weight: 500;
  margin-right: 16px;
  text-decoration: none;
  transition: color 0.2s;
}
.login-link:hover {
  color: #2563eb;
}
.register-link {
  background: #2563eb;
  color: #fff;
  padding: 8px 16px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background 0.2s;
}
.register-link:hover {
  background: #1d4ed8;
}

.hero-section {
  position: relative;
  height: 76vh;
  background-image: url('/src/assets/hero-banner.png');
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #fff;
}
.hero-overlay {
  background: rgba(0, 0, 0, 0.6);
  padding: 40px;
  border-radius: 16px;
  width: 100%;
  max-width: 768px;
  margin: 0 auto;
}
.hero-title {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.1;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}
.hero-desc {
  margin-top: 24px;
  font-size: 1.25rem;
  color: #fff;
  opacity: 0.92;
  font-weight: 500;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  padding: 0 16px;
}
.hero-btn-row {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
}
.hero-btn-blue {
  background: #2563eb;
  color: #fff;
  padding: 12px 28px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1.125rem;
  text-decoration: none;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
  transition: background 0.2s;
}
.hero-btn-blue:hover {
  background: #1d4ed8;
}
.hero-btn-blur {
  background: rgba(156, 163, 175, 0.6);
  color: #fff;
  padding: 12px 28px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1.125rem;
  text-decoration: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(4px);
  transition: background 0.2s;
}
.hero-btn-blur:hover {
  background: rgba(107, 114, 128, 0.7);
}

.why-section {
  background: #f9fafb;
  padding: 80px 24px;
  text-align: center;
}

.why-container {
  max-width: 1200px;
  margin: 0 auto;
}

.why-title {
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
}

.why-subtitle {
  color: #6b7280;
  font-size: 1rem;
  margin-bottom: 48px;
}

.why-features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.why-card {
  background: #ffffff;
  padding: 32px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
  transition: transform 0.2s;
}

.why-card:hover {
  transform: translateY(-4px);
}

.why-icon {
  background: #eef2ff;
  border-radius: 12px;
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.why-icon img {
  width: 24px;
  height: 24px;
}

.why-card h3 {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}

.why-card p {
  font-size: 0.9375rem;
  color: #6b7280;
}

/* Real-time Analytics Section */
.analytics-section {
  background: #fff;
  padding: 80px 24px;
}

.analytics-container {
  display: flex;
  flex-wrap: wrap;
  max-width: 1200px;
  margin: 0 auto;
  align-items: center;
  gap: 48px;
  justify-content: space-between;
}

.analytics-text {
  flex: 1;
  min-width: 320px;
}

.analytics-text h2 {
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 16px;
}

.analytics-text p {
  font-size: 1rem;
  color: #4b5563;
  margin-bottom: 24px;
  line-height: 1.6;
}

.analytics-text ul {
  list-style: none;
  padding: 0;
}

.analytics-text ul li {
  margin-bottom: 12px;
  font-size: 1rem;
  color: #10b981;
}

.analytics-image {
  flex: 1;
  min-width: 320px;
}

.analytics-image img {
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* CTA Section */
.cta-section {
  background: #2563eb;
  color: white;
  text-align: center;
  padding: 64px 24px;
}

.cta-section h2 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.cta-section p {
  font-size: 1rem;
  opacity: 0.9;
  margin-bottom: 28px;
}

.cta-button {
  display: inline-block;
  background: white;
  color: #2563eb;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  transition: background 0.2s;
}

.cta-button:hover {
  background: #f3f4f6;
}

/* Footer Section */
.footer-section {
  background-color: #0f172a;
  color: #cbd5e1;
  padding: 48px 24px 20px;
  font-size: 0.9375rem;
}

.footer-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 64px;
  max-width: 900px;
  margin: 0 auto;
  padding-bottom: 24px;
  text-align: left;
}

.footer-left {
  max-width: 400px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.footer-logo {
  height: 28px;
  width: 28px;
  object-fit: contain;
}

.footer-title {
  font-weight: 700;
  font-size: 1.25rem;
  color: #ffffff;
}

.footer-desc {
  color: #94a3b8;
  margin-top: 4px;
  line-height: 1.5;
}

.footer-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-right a {
  color: #60a5fa;
  text-decoration: none;
}

.footer-right a:hover {
  text-decoration: underline;
}

.footer-bottom {
  text-align: center;
  margin-top: 32px;
  font-size: 0.875rem;
  color: #64748b;
  border-top: 1px solid #1e293b;
  padding-top: 16px;
}
</style>
