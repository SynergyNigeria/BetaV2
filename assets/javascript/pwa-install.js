// PWA Installation Handler
let deferredPrompt;
let installButton;

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
  installButton = document.getElementById('pwa-install-btn');
  
  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('App is already installed');
    hideInstallButton();
    return;
  }
  
  // Check if iOS device
  if (isIOS()) {
    console.log('iOS device detected');
    // Show button for iOS with different behavior
    if (installButton) {
      installButton.onclick = showIOSInstallInstructions;
      showInstallButton();
    }
  } else {
    // For non-iOS, show button and wait for beforeinstallprompt
    showInstallButton();
  }
  
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  }
});

// Register Service Worker
async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/'
    });
    
    console.log('Service Worker registered successfully:', registration.scope);
    
    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('New Service Worker found');
      
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available
          showUpdateNotification();
        }
      });
    });
  } catch (error) {
    console.error('Service Worker registration failed:', error);
  }
}

// Listen for beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('beforeinstallprompt event fired');
  
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  
  // Show the install button
  showInstallButton();
});

// Install button click handler
function installPWA() {
  if (!deferredPrompt) {
    console.log('Install prompt not available yet');
    
    // Show helpful message
    const message = document.createElement('div');
    message.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
    message.innerHTML = `
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <span>Installation will be available soon. Keep using the app!</span>
      </div>
    `;
    document.body.appendChild(message);
    
    setTimeout(() => {
      message.remove();
    }, 4000);
    return;
  }
  
  // Hide the install button
  hideInstallButton();
  
  // Show the install prompt
  deferredPrompt.prompt();
  
  // Wait for the user to respond to the prompt
  deferredPrompt.userChoice.then((choiceResult) => {
    if (choiceResult.outcome === 'accepted') {
      console.log('User accepted the install prompt');
      showInstallSuccess();
    } else {
      console.log('User dismissed the install prompt');
      // Show button again after 1 minute
      setTimeout(() => {
        showInstallButton();
      }, 60000);
    }
    
    // Clear the deferredPrompt
    deferredPrompt = null;
  });
}

// Listen for app installed event
window.addEventListener('appinstalled', (e) => {
  console.log('BetaBank PWA was installed');
  hideInstallButton();
  showInstallSuccess();
});

// Show install button
function showInstallButton() {
  if (installButton) {
    installButton.style.display = 'flex';
    installButton.classList.add('fade-in');
  }
}

// Hide install button
function hideInstallButton() {
  if (installButton) {
    installButton.style.display = 'none';
  }
}

// Show install success message
function showInstallSuccess() {
  const successMessage = document.createElement('div');
  successMessage.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
  successMessage.innerHTML = `
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
      </svg>
      <span>BetaBank installed successfully!</span>
    </div>
  `;
  document.body.appendChild(successMessage);
  
  setTimeout(() => {
    successMessage.remove();
  }, 3000);
}

// Show update notification
function showUpdateNotification() {
  const updateBanner = document.createElement('div');
  updateBanner.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
  updateBanner.innerHTML = `
    <div class="flex items-center gap-4">
      <span>New version available!</span>
      <button onclick="updatePWA()" class="bg-white text-blue-600 px-4 py-1 rounded font-semibold">
        Update
      </button>
    </div>
  `;
  document.body.appendChild(updateBanner);
}

// Update PWA
function updatePWA() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistration().then((registration) => {
      if (registration && registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      }
    });
  }
}

// Check if device is iOS
function isIOS() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

// Show iOS install instructions
function showIOSInstallInstructions() {
  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
  modal.innerHTML = `
    <div class="bg-white rounded-xl p-6 max-w-md">
      <h3 class="text-xl font-bold mb-4">Install BetaBank</h3>
      <p class="mb-4">To install this app on your iOS device:</p>
      <ol class="list-decimal list-inside space-y-2 mb-4">
        <li>Tap the Share button <span class="inline-block">⬆️</span></li>
        <li>Scroll down and tap "Add to Home Screen"</li>
        <li>Tap "Add" in the top right corner</li>
      </ol>
      <button onclick="this.closest('.fixed').remove()" class="w-full bg-purple-600 text-white py-2 rounded-lg font-semibold">
        Got it!
      </button>
    </div>
  `;
  document.body.appendChild(modal);
}

// Export functions for global use
window.installPWA = installPWA;
window.updatePWA = updatePWA;
window.showIOSInstallInstructions = showIOSInstallInstructions;
window.isIOS = isIOS;
