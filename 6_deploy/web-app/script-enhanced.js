// Enhanced Virtual Coffee Shop Script - Direct AgentCore Integration
console.log('🚀 Loading Enhanced Script with Direct AgentCore Integration');

const chatbotForm = document.getElementById('chatbot-form');
const chatbotInput = document.getElementById('chatbot-input');
const chatbotMessages = document.getElementById('chatbot-messages');
const signOutButton = document.getElementById('signOutButton');

let isInitialized = false;

// Add sign out functionality
if (signOutButton) {
    signOutButton.addEventListener('click', function() {
        window.CognitoAuth.signOut();
    });
}

// Initialize the application
async function initializeApp() {
    try {
        console.log('Initializing application...');
        
        // Step 1: Load Cognito configuration
        console.log('Step 1: Loading Cognito configuration...');
        await window.CognitoAuth.loadCognitoConfig();
        console.log('✅ Cognito configuration loaded');
        
        // Step 2: Initialize AgentCore client
        console.log('Step 2: Initializing AgentCore client...');
        try {
            await window.fixedAgentCoreClient.initialize();
            console.log('✅ Fixed AgentCore client initialized');
        } catch (error) {
            console.error('❌ Failed to initialize AgentCore client:', error);
            throw error;
        }
        
        // Step 3: Load stores data
        console.log('Step 3: Loading stores data...');
        await loadStoreData();
        console.log('✅ Stores data loaded');
        
        isInitialized = true;
        console.log('✅ Application initialized successfully');
        
        // Clear any existing messages and add personalized greeting
        chatbotMessages.innerHTML = '';
        
        // Add personalized greeting
        addPersonalizedGreeting();
        
        // Add welcome message
        addMessage('Welcome to the Virtual Coffee Shop! I can help you with orders, store information, and more. How can I assist you today?', 'bot');
        
    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        
        // Show more specific error message
        let errorMessage = 'Sorry, there was an error initializing the application. ';
        if (error.message.includes('AgentCore')) {
            errorMessage += 'AgentCore service issue detected. ';
        } else if (error.message.includes('Cognito')) {
            errorMessage += 'Authentication service issue detected. ';
        } else if (error.message.includes('stores')) {
            errorMessage += 'Store data loading issue detected. ';
        }
        errorMessage += 'Please check the browser console for details and try refreshing the page.';
        
        addMessage(errorMessage, 'bot');
    }
}

// Add personalized greeting
function addPersonalizedGreeting() {
    // Get username from session storage
    const username = sessionStorage.getItem('username');
    
    // Get current time and determine greeting
    const now = new Date();
    const hour = now.getHours();
    
    let timeGreeting;
    if (hour >= 5 && hour < 12) {
        timeGreeting = "Good morning";
    } else if (hour >= 12 && hour < 17) {
        timeGreeting = "Good afternoon";
    } else {
        timeGreeting = "Good evening";
    }
    
    // Create personalized greeting
    let greeting;
    if (username) {
        greeting = `${timeGreeting}, ${username}! What would you like to order today?`;
    } else {
        greeting = `${timeGreeting}! What would you like to order today?`;
    }
    
    // Add as first message
    addMessage(greeting, 'bot');
    console.log('Personalized greeting added:', greeting);
}

// Store data management
let storesData = [];

async function loadStoreData() {
    try {
        const response = await fetch('stores_records.json');
        storesData = await response.json();
        console.log('Stores data loaded:', storesData.length, 'stores');
        populateStoreDropdown();
    } catch (error) {
        console.error('Error loading stores data:', error);
    }
}

function populateStoreDropdown() {
    const storeDropdown = document.getElementById('store-dropdown');
    const storeDropdownMenu = document.getElementById('store-dropdown-menu');
    
    if (!storeDropdown || !storeDropdownMenu) {
        console.warn('Store dropdown elements not found');
        return;
    }

    // Clear existing options
    storeDropdownMenu.innerHTML = '';

    // Group stores by city and state
    const groupedStores = {};
    storesData.forEach(store => {
        const key = `${store.city}, ${store.state}`;
        if (!groupedStores[key]) {
            groupedStores[key] = [];
        }
        groupedStores[key].push(store);
    });

    // Create dropdown items
    Object.keys(groupedStores).sort().forEach(cityState => {
        // Add city header
        const cityHeader = document.createElement('div');
        cityHeader.className = 'store-city-header';
        cityHeader.textContent = cityState;
        storeDropdownMenu.appendChild(cityHeader);

        // Add stores for this city
        groupedStores[cityState].forEach(store => {
            const storeItem = document.createElement('div');
            storeItem.className = 'store-item';
            storeItem.onclick = () => selectStore(store);
            
            const storeName = document.createElement('div');
            storeName.className = 'store-name';
            storeName.textContent = store.name;
            
            const storeAddress = document.createElement('div');
            storeAddress.className = 'store-address';
            storeAddress.textContent = store.address;
            
            storeItem.appendChild(storeName);
            storeItem.appendChild(storeAddress);
            
            if (store.has_drive_thru) {
                const driveThruBadge = document.createElement('span');
                driveThruBadge.className = 'drive-thru-badge';
                driveThruBadge.textContent = 'Drive-Thru';
                storeItem.appendChild(driveThruBadge);
            }
            
            storeDropdownMenu.appendChild(storeItem);
        });
    });
}

function selectStore(store) {
    console.log('Store selected:', store);
    
    // Store the selected store in session storage
    sessionStorage.setItem('selectedStore', JSON.stringify(store));
    
    // Update the dropdown button text
    const storeButton = document.querySelector('#store-dropdown .dropdown-button');
    if (storeButton) {
        storeButton.innerHTML = `
            <span class="selected-store-info">
                <strong>${store.name}</strong><br>
                <small>${store.address}</small>
            </span>
            <span class="dropdown-arrow">▼</span>
        `;
    }
    
    // Close the dropdown
    const storeDropdownMenu = document.getElementById('store-dropdown-menu');
    if (storeDropdownMenu) {
        storeDropdownMenu.style.display = 'none';
    }
    
    // Update the selected store display
    updateSelectedStoreDisplay(store);
    
    // Notify the user
    addMessage(`Great! I've selected ${store.name} at ${store.address} for your order.`, 'bot');
}

function updateSelectedStoreDisplay(store) {
    const selectedStoreDiv = document.getElementById('selected-store');
    if (selectedStoreDiv) {
        selectedStoreDiv.innerHTML = `
            <div class="selected-store-info">
                <h4>${store.name}</h4>
                <p>${store.address}</p>
                <p>${store.city}, ${store.state} ${store.zip_code}</p>
                ${store.has_drive_thru ? '<span class="drive-thru-badge">Drive-Thru Available</span>' : ''}
                <p class="store-hours">Hours: ${store.hours_start} - ${store.hours_end}</p>
            </div>
        `;
        selectedStoreDiv.style.display = 'block';
    }
}

// Dropdown functionality
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    const menu = dropdown.querySelector('.dropdown-menu');
    if (!menu) return;
    
    const isVisible = menu.style.display === 'block';
    
    // Close all dropdowns first
    document.querySelectorAll('.dropdown-menu').forEach(d => {
        d.style.display = 'none';
    });
    
    // Toggle the clicked dropdown
    menu.style.display = isVisible ? 'none' : 'block';
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    }
});

// Message handling
function addMessage(message, sender, isLoading = false) {
    const messageDiv = document.createElement('div');
    
    // Use the correct CSS classes that match the existing styles
    if (sender === 'bot') {
        messageDiv.classList.add('bot-message');
    } else if (sender === 'user') {
        messageDiv.classList.add('user-message');
    }
    
    if (isLoading) {
        messageDiv.classList.add('loading-message');
        messageDiv.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <span class="loading-text">Processing your request...</span>
            </div>
        `;
    } else {
        messageDiv.textContent = message;
    }
    
    chatbotMessages.appendChild(messageDiv);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    
    return messageDiv;
}

function removeMessage(messageElement) {
    if (messageElement && messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
    }
}

// Sample prompt functionality
function sendSamplePrompt(promptText) {
    const chatInput = document.getElementById('chatbot-input');
    if (chatInput) {
        chatInput.value = promptText;
        chatInput.focus();
        
        // Optional: Auto-send the message after a short delay
        setTimeout(() => {
            const chatForm = document.getElementById('chatbot-form');
            if (chatForm) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }, 500);
    }
}

// Make function globally available
window.sendSamplePrompt = sendSamplePrompt;

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (!isInitialized) {
        addMessage('Please wait while the application initializes...', 'bot');
        return;
    }
    
    const userInput = chatbotInput.value.trim();
    if (!userInput) return;
    
    // Add user message
    addMessage(userInput, 'user');
    
    // Clear input
    chatbotInput.value = '';
    
    // Add loading message
    const loadingMessage = addMessage('', 'bot', true);
    
    try {
        // Get selected store if any
        const selectedStoreData = sessionStorage.getItem('selectedStore');
        const selectedStore = selectedStoreData ? JSON.parse(selectedStoreData) : null;
        
        // Send message to AgentCore using the fixed client
        const response = await window.fixedAgentCoreClient.sendMessage(userInput);
        
        // Remove loading message
        removeMessage(loadingMessage);
        
        // Add bot response
        if (response && response.message) {
            addMessage(response.message, 'bot');
        } else {
            addMessage('I received your message but there was no response. Please try again.', 'bot');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Remove loading message
        removeMessage(loadingMessage);
        
        // Show error message
        let errorMessage = 'Sorry, I encountered an error processing your request.';
        if (error.message.includes('Access denied')) {
            errorMessage = 'Access denied. Please try logging out and logging back in.';
        } else if (error.message.includes('not found')) {
            errorMessage = 'The service is currently unavailable. Please try again later.';
        }
        
        addMessage(errorMessage, 'bot');
    }
}

// Event listeners
if (chatbotForm) {
    chatbotForm.addEventListener('submit', handleFormSubmit);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    initializeApp();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && !isInitialized) {
        console.log('Page became visible, reinitializing...');
        initializeApp();
    }
});

console.log('Enhanced script loaded successfully');
