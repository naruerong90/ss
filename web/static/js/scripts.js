/*!
 * ShopCounter Admin Theme v1.0.0
 * Based on SB Admin (MIT License)
 */

:root {
    --primary: #4e73df;
    --secondary: #858796;
    --success: #1cc88a;
    --info: #36b9cc;
    --warning: #f6c23e;
    --danger: #e74a3b;
    --light: #f8f9fc;
    --dark: #5a5c69;
  }
  
  /* 
   * Global Styles
   */
  html, body {
    height: 100%;
  }
  
  body {
    font-family: 'Noto Sans Thai', 'Nunito', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    color: #212529;
    background-color: #f8f9fc;
  }
  
  .card {
    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
  }
  
  .card .card-header {
    font-weight: 500;
  }
  
  .table-responsive {
    overflow-x: auto;
  }
  
  /*
   * Layout - Sidebar & Topbar
   */
  #layoutSidenav {
    display: flex;
  }
  
  #layoutSidenav #layoutSidenav_nav {
    flex-basis: 225px;
    flex-shrink: 0;
    transition: transform 0.15s ease-in-out;
    z-index: 1038;
    transform: translateX(-225px);
  }
  
  #layoutSidenav #layoutSidenav_content {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-width: 0;
    flex-grow: 1;
    min-height: calc(100vh - 56px);
    margin-left: -225px;
  }
  
  .sb-sidenav-toggled #layoutSidenav #layoutSidenav_nav {
    transform: translateX(0);
  }
  
  .sb-sidenav-toggled #layoutSidenav #layoutSidenav_content:before {
    content: "";
    display: block;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #000;
    z-index: 1037;
    opacity: 0.5;
    transition: opacity 0.3s ease-in-out;
  }
  
  @media (min-width: 992px) {
    #layoutSidenav #layoutSidenav_nav {
      transform: translateX(0);
    }
    #layoutSidenav #layoutSidenav_content {
      margin-left: 0;
      transition: margin 0.15s ease-in-out;
    }
  
    .sb-sidenav-toggled #layoutSidenav #layoutSidenav_nav {
      transform: translateX(-225px);
    }
    .sb-sidenav-toggled #layoutSidenav #layoutSidenav_content {
      margin-left: -225px;
    }
    .sb-sidenav-toggled #layoutSidenav #layoutSidenav_content:before {
      display: none;
    }
  }
  
  .sb-topnav {
    padding-left: 0;
    height: 56px;
    z-index: 1039;
  }
  
  .sb-topnav .navbar-brand {
    width: 225px;
    padding-left: 1rem;
    padding-right: 1rem;
    margin: 0;
  }
  
  .sb-topnav.navbar-dark #sidebarToggle {
    color: rgba(255, 255, 255, 0.5);
  }
  
  .sb-topnav.navbar-light #sidebarToggle {
    color: #212529;
  }
  
  .sb-sidenav {
    display: flex;
    flex-direction: column;
    height: 100%;
    flex-wrap: nowrap;
  }
  
  .sb-sidenav .sb-sidenav-menu {
    flex-grow: 1;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav {
    flex-direction: column;
    flex-wrap: nowrap;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .sb-sidenav-menu-heading {
    padding: 1.75rem 1rem 0.75rem;
    font-size: 0.75rem;
    font-weight: bold;
    text-transform: uppercase;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .nav-link {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    position: relative;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .nav-link .sb-nav-link-icon {
    font-size: 0.9rem;
    margin-right: 0.5rem;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .nav-link .sb-sidenav-collapse-arrow {
    display: inline-block;
    margin-left: auto;
    transition: transform 0.15s ease;
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .nav-link.collapsed .sb-sidenav-collapse-arrow {
    transform: rotate(-90deg);
  }
  
  .sb-sidenav .sb-sidenav-menu .nav .sb-sidenav-menu-nested {
    margin-left: 1.5rem;
    flex-direction: column;
  }
  
  .sb-sidenav .sb-sidenav-footer {
    padding: 0.75rem;
    flex-shrink: 0;
  }
  
  .sb-sidenav-dark {
    background-color: #212529;
    color: rgba(255, 255, 255, 0.5);
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .sb-sidenav-menu-heading {
    color: rgba(255, 255, 255, 0.25);
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .nav-link {
    color: rgba(255, 255, 255, 0.5);
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .nav-link .sb-nav-link-icon {
    color: rgba(255, 255, 255, 0.25);
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .nav-link:hover {
    color: #fff;
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .nav-link.active {
    color: #fff;
  }
  
  .sb-sidenav-dark .sb-sidenav-menu .nav-link.active .sb-nav-link-icon {
    color: #fff;
  }
  
  .sb-sidenav-dark .sb-sidenav-footer {
    background-color: #343a40;
  }
  
  .sb-sidenav-light {
    background-color: #f8f9fa;
    color: #212529;
  }
  
  .sb-sidenav-light .sb-sidenav-menu .sb-sidenav-menu-heading {
    color: #adb5bd;
  }
  
  .sb-sidenav-light .sb-sidenav-menu .nav-link {
    color: #212529;
  }
  
  .sb-sidenav-light .sb-sidenav-menu .nav-link .sb-nav-link-icon {
    color: #adb5bd;
  }
  
  .sb-sidenav-light .sb-sidenav-menu .nav-link:hover {
    color: var(--primary);
  }
  
  .sb-sidenav-light .sb-sidenav-menu .nav-link.active {
    color: var(--primary);
  }
  
  .sb-sidenav-light .sb-sidenav-menu .nav-link.active .sb-nav-link-icon {
    color: var(--primary);
  }
  
  .sb-sidenav-light .sb-sidenav-footer {
    background-color: #e9ecef;
  }
  
  /* 
   * Dashboard Cards
   */
  .card .card-body .h1 {
    font-size: 2.25rem;
    font-weight: 700;
  }
  
  .card .card-body .h3 {
    font-size: 1.5rem;
    font-weight: 700;
  }
  
  /* 
   * Login Page
   */
  #layoutAuthentication {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  
  #layoutAuthentication #layoutAuthentication_content {
    min-width: 0;
    flex-grow: 1;
  }
  
  #layoutAuthentication #layoutAuthentication_footer {
    min-width: 0;
  }
  
  .bg-login-image {
    background: url("../images/login-bg.jpg");
    background-position: center;
    background-size: cover;
  }
  
  .bg-register-image {
    background: url("../images/register-bg.jpg");
    background-position: center;
    background-size: cover;
  }
  
  .bg-password-image {
    background: url("../images/password-bg.jpg");
    background-position: center;
    background-size: cover;
  }
  
  .form-floating.mb-3 .form-control {
    border-radius: 10rem;
    padding: 1.5rem 1rem;
  }
  
  .form-floating.mb-3 label {
    padding: 1.5rem 1rem;
  }
  
  .btn-user {
    border-radius: 10rem;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
  
  /* 
   * Error page
   */
  .error-page {
    background-color: #f8f9fc;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .error-code {
    font-size: 8rem;
    font-weight: 800;
    color: var(--primary);
  }
  
  /* 
   * Custom Components
   */
  .border-left-primary {
    border-left: 0.25rem solid var(--primary) !important;
  }
  
  .border-left-secondary {
    border-left: 0.25rem solid var(--secondary) !important;
  }
  
  .border-left-success {
    border-left: 0.25rem solid var(--success) !important;
  }
  
  .border-left-info {
    border-left: 0.25rem solid var(--info) !important;
  }
  
  .border-left-warning {
    border-left: 0.25rem solid var(--warning) !important;
  }
  
  .border-left-danger {
    border-left: 0.25rem solid var(--danger) !important;
  }
  
  .border-bottom-primary {
    border-bottom: 0.25rem solid var(--primary) !important;
  }
  
  .border-bottom-secondary {
    border-bottom: 0.25rem solid var(--secondary) !important;
  }
  
  .border-bottom-success {
    border-bottom: 0.25rem solid var(--success) !important;
  }
  
  .border-bottom-info {
    border-bottom: 0.25rem solid var(--info) !important;
  }
  
  .border-bottom-warning {
    border-bottom: 0.25rem solid var(--warning) !important;
  }
  
  .border-bottom-danger {
    border-bottom: 0.25rem solid var(--danger) !important;
  }
  
  .progress-sm {
    height: 0.5rem;
  }
  
  .rotate-15 {
    transform: rotate(15deg);
  }
  
  .rotate-n-15 {
    transform: rotate(-15deg);
  }
  
  .dropdown .dropdown-menu {
    font-size: 0.85rem;
  }
  
  .dropdown .dropdown-menu .dropdown-header {
    font-weight: 800;
    font-size: 0.65rem;
    color: #b7b9cc;
  }
  
  .dropdown.no-arrow .dropdown-toggle::after {
    display: none;
  }
  
  .dropdown-item:active {
    color: #fff;
    background-color: var(--primary);
  }
  
  /* 
   * Custom utilities
   */
  .text-gray-100 {
    color: #f8f9fc !important;
  }
  
  .text-gray-200 {
    color: #eaecf4 !important;
  }
  
  .text-gray-300 {
    color: #dddfeb !important;
  }
  
  .text-gray-400 {
    color: #d1d3e2 !important;
  }
  
  .text-gray-500 {
    color: #b7b9cc !important;
  }
  
  .text-gray-600 {
    color: #858796 !important;
  }
  
  .text-gray-700 {
    color: #6e707e !important;
  }
  
  .text-gray-800 {
    color: #5a5c69 !important;
  }
  
  .text-gray-900 {
    color: #3a3b45 !important;
  }
  
  .shadow-light {
    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1) !important;
  }
  
  .shadow-dark {
    box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.25) !important;
  }
  
  /* 
   * Custom Scroll Bars
   */
   ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }
  
  ::-webkit-scrollbar-track {
    background: #f1f1f1; 
  }
   
  ::-webkit-scrollbar-thumb {
    background: #888; 
    border-radius: 5px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: #555; 
  }
  
  /* 
   * Responsive overrides
   */
  @media (min-width: 768px) {
    .chart-area {
      height: 20rem;
    }
    .chart-bar {
      height: 20rem;
    }
    .chart-pie {
      height: 20rem;
    }
  }
  
  @media (max-width: 767.98px) {
    .chart-area {
      height: 15rem;
    }
    .chart-bar {
      height: 15rem;
    }
    .chart-pie {
      height: 15rem;
    }
  }
  
  /* 
   * Data Tables
   */
  .dataTables_wrapper .dataTables_length, 
  .dataTables_wrapper .dataTables_filter, 
  .dataTables_wrapper .dataTables_info, 
  .dataTables_wrapper .dataTables_processing, 
  .dataTables_wrapper .dataTables_paginate {
    font-size: 0.85rem;
  }
  
  /* Thai Language Font */
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
  
  /* Smaller mobile table optimization */
  @media (max-width: 767.98px) {
    table.responsive {
      font-size: 0.8rem;
    }
    table.responsive th,
    table.responsive td {
      padding: 0.5rem;
    }
  }