/**
 * EduPath AI Chatbot Component
 * A reusable AI chatbot that can be integrated into any page
 */

class EduPathChatbot {
    constructor(options = {}) {
        this.options = {
            position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
            theme: 'blue', // blue, purple, green, dark
            welcomeMessage: 'Hi! I\'m your AI assistant. How can I help you today?',
            ...options
        };
        
        this.isOpen = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.createChatbotHTML();
        this.attachEventListeners();
        this.addWelcomeMessage();
    }

    createChatbotHTML() {
        const chatbotHTML = `
            <div id="edupath-chatbot" class="fixed ${this.getPositionClass()} z-50">
                <div id="chat-window" class="hidden mb-4 w-80 h-96 bg-white rounded-2xl shadow-2xl overflow-hidden">
                    <div class="bg-gradient-to-r ${this.getThemeGradient()} p-4 text-white">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <div class="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                    <span class="material-symbols-outlined text-sm">smart_toy</span>
                                </div>
                                <h3 class="font-semibold">EduPath AI Assistant</h3>
                            </div>
                            <button id="close-chat" class="text-white/80 hover:text-white">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>
                    </div>
                    <div id="chat-messages" class="h-64 overflow-y-auto p-4 space-y-3">
                        <!-- Messages will be added here -->
                    </div>
                    <div class="p-4 border-t">
                        <div class="flex space-x-2">
                            <input type="text" id="chat-input" placeholder="Ask me anything..." 
                                   class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <button id="send-message" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                                <span class="material-symbols-outlined text-sm">send</span>
                            </button>
                        </div>
                    </div>
                </div>
                <button id="chat-toggle" class="w-14 h-14 bg-white rounded-full shadow-lg flex items-center justify-center hover:shadow-xl transition-all floating">
                    <span class="material-symbols-outlined text-blue-500">chat</span>
                </button>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    getPositionClass() {
        const positions = {
            'bottom-right': 'bottom-6 right-6',
            'bottom-left': 'bottom-6 left-6',
            'top-right': 'top-6 right-6',
            'top-left': 'top-6 left-6'
        };
        return positions[this.options.position] || positions['bottom-right'];
    }

    getThemeGradient() {
        const themes = {
            'blue': 'from-blue-500 to-blue-600',
            'purple': 'from-purple-500 to-purple-600',
            'green': 'from-green-500 to-green-600',
            'dark': 'from-gray-700 to-gray-800'
        };
        return themes[this.options.theme] || themes['blue'];
    }

    attachEventListeners() {
        const toggleBtn = document.getElementById('chat-toggle');
        const closeBtn = document.getElementById('close-chat');
        const sendBtn = document.getElementById('send-message');
        const chatInput = document.getElementById('chat-input');

        toggleBtn.addEventListener('click', () => this.toggleChat());
        closeBtn.addEventListener('click', () => this.closeChat());
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    addWelcomeMessage() {
        this.addMessage(this.options.welcomeMessage, 'ai');
    }

    toggleChat() {
        const chatWindow = document.getElementById('chat-window');
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            chatWindow.classList.remove('hidden');
            document.getElementById('chat-input').focus();
        } else {
            chatWindow.classList.add('hidden');
        }
    }

    closeChat() {
        const chatWindow = document.getElementById('chat-window');
        this.isOpen = false;
        chatWindow.classList.add('hidden');
    }

    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        this.addMessage(message, 'user');
        input.value = '';

        // Simulate AI response
        setTimeout(() => {
            const response = this.generateAIResponse(message);
            this.addMessage(response, 'ai');
        }, 1000);
    }

    addMessage(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-bubble';

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="flex justify-end">
                    <div class="bg-blue-500 text-white rounded-lg p-3 max-w-xs">
                        <p class="text-sm">${this.escapeHtml(message)}</p>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="flex items-start space-x-2">
                    <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <span class="material-symbols-outlined text-blue-600 text-xs">smart_toy</span>
                    </div>
                    <div class="bg-gray-100 rounded-lg p-3 max-w-xs">
                        <p class="text-sm text-gray-700">${this.escapeHtml(message)}</p>
                    </div>
                </div>
            `;
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        this.messages.push({ message, sender, timestamp: new Date() });
    }

    generateAIResponse(message) {
        const lowerMessage = message.toLowerCase();
        const currentPage = this.getCurrentPageContext();

        // Page-specific responses
        if (currentPage === 'login') {
            return this.getLoginResponse(lowerMessage);
        } else if (currentPage === 'register') {
            return this.getRegistrationResponse(lowerMessage);
        } else if (currentPage === 'quiz') {
            return this.getQuizResponse(lowerMessage);
        } else if (currentPage === 'colleges') {
            return this.getCollegesResponse(lowerMessage);
        } else if (currentPage === 'careers') {
            return this.getCareersResponse(lowerMessage);
        } else if (currentPage === 'resources') {
            return this.getResourcesResponse(lowerMessage);
        } else if (currentPage === 'profile') {
            return this.getProfileResponse(lowerMessage);
        }

        // General responses
        return this.getGeneralResponse(lowerMessage);
    }

    getCurrentPageContext() {
        const path = window.location.pathname;
        if (path.includes('login')) return 'login';
        if (path.includes('register')) return 'register';
        if (path.includes('quiz')) return 'quiz';
        if (path.includes('colleges')) return 'colleges';
        if (path.includes('career')) return 'careers';
        if (path.includes('resources')) return 'resources';
        if (path.includes('profile')) return 'profile';
        return 'home';
    }

    getLoginResponse(message) {
        const responses = {
            'password': 'For security, use a strong password with at least 8 characters, including uppercase, lowercase, numbers, and symbols.',
            'forgot': 'If you forgot your password, click the "Forgot password?" link below the login form. We\'ll send you a reset link.',
            'account': 'Don\'t have an account? Click "Sign up for free" to create one. It only takes 2 minutes!',
            'help': 'I can help with login issues, account creation, password recovery, or any questions about our platform. What do you need?'
        };
        return this.findBestResponse(message, responses) || 'I\'m here to help with your login! What specific issue are you facing?';
    }

    getRegistrationResponse(message) {
        const responses = {
            'password': 'For a strong password, use at least 8 characters with a mix of uppercase, lowercase, numbers, and symbols. Avoid common words.',
            'career': 'Think about what activities you enjoy most. Do you like problem-solving, helping people, creating things, or analyzing data?',
            'email': 'Use a professional email address that you check regularly. This will be important for receiving career guidance.',
            'interest': 'Your career interest helps our AI recommend relevant colleges, courses, and career paths. You can change this later.',
            'help': 'I can help with form validation, career interest selection, and explain any part of the signup process. What would you like to know?'
        };
        return this.findBestResponse(message, responses) || 'I\'m here to help with your registration! What would you like to know?';
    }

    getQuizResponse(message) {
        const responses = {
            'career': 'Our career quiz analyzes your interests, skills, and personality to suggest the best career paths for you. Just answer honestly!',
            'question': 'Each question helps us understand your preferences better. There are no right or wrong answers.',
            'result': 'After completing the quiz, you\'ll get personalized career recommendations and college suggestions.',
            'help': 'I can explain the quiz process, help with questions, or guide you through the results. What do you need?'
        };
        return this.findBestResponse(message, responses) || 'I can help you with the career assessment quiz. What would you like to know?';
    }

    getCollegesResponse(message) {
        const responses = {
            'college': 'I can help you find colleges that match your interests and career goals. What field are you interested in?',
            'admission': 'College admissions typically require good grades, test scores, essays, and extracurricular activities. I can guide you through the process.',
            'cost': 'College costs vary widely. I can help you find scholarships, financial aid, and affordable options.',
            'help': 'I can help with college selection, admission requirements, costs, and finding the right fit for you.'
        };
        return this.findBestResponse(message, responses) || 'I can help you explore colleges and universities. What would you like to know?';
    }

    getCareersResponse(message) {
        const responses = {
            'career': 'I can help you explore different career paths based on your interests and skills. What field interests you?',
            'salary': 'Career salaries vary by field, experience, and location. I can provide general salary ranges for different careers.',
            'skills': 'Different careers require different skills. I can help you identify what skills you need to develop.',
            'help': 'I can help with career exploration, skill development, and finding the right career path for you.'
        };
        return this.findBestResponse(message, responses) || 'I can help you explore career options and plan your professional future. What interests you?';
    }

    getResourcesResponse(message) {
        const responses = {
            'study': 'I can recommend study materials, techniques, and resources based on your subjects and learning style.',
            'book': 'Our resource library includes e-books, videos, practice tests, and study guides for various subjects.',
            'help': 'I can help you find the right study materials, recommend learning strategies, and guide your academic journey.'
        };
        return this.findBestResponse(message, responses) || 'I can help you find the right study materials and resources. What subject are you studying?';
    }

    getProfileResponse(message) {
        const responses = {
            'profile': 'I can help you update your profile, manage your preferences, and track your progress.',
            'recommendation': 'Your profile helps me provide personalized recommendations for colleges, careers, and study materials.',
            'help': 'I can help you manage your profile, update your information, and optimize your recommendations.'
        };
        return this.findBestResponse(message, responses) || 'I can help you manage your profile and get personalized recommendations. What would you like to update?';
    }

    getGeneralResponse(message) {
        const responses = {
            'hello': 'Hello! I\'m your AI assistant. I can help with career guidance, college selection, study tips, and more. How can I assist you?',
            'help': 'I can help with career guidance, college selection, study materials, quiz assistance, and general questions about our platform.',
            'career': 'I can help you explore career options, find the right path, and plan your professional future. What interests you?',
            'college': 'I can help you find colleges, understand admission requirements, and choose the right institution for your goals.',
            'study': 'I can recommend study materials, techniques, and resources to help you succeed academically.',
            'quiz': 'I can help you with our career assessment quiz and explain the results.',
            'default': 'I\'m here to help with your career and education journey! I can assist with career guidance, college selection, study tips, and more. What would you like to know?'
        };
        return this.findBestResponse(message, responses) || responses.default;
    }

    findBestResponse(message, responses) {
        for (const [key, response] of Object.entries(responses)) {
            if (message.includes(key)) {
                return response;
            }
        }
        return null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Public methods for external control
    open() {
        if (!this.isOpen) {
            this.toggleChat();
        }
    }

    close() {
        if (this.isOpen) {
            this.toggleChat();
        }
    }

    addSystemMessage(message) {
        this.addMessage(message, 'ai');
    }

    getChatHistory() {
        return this.messages;
    }
}

// Auto-initialize chatbot if not already present
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('edupath-chatbot')) {
        window.edupathChatbot = new EduPathChatbot({
            position: 'bottom-right',
            theme: 'blue',
            welcomeMessage: 'Hi! I\'m your AI assistant. I can help with career guidance, college selection, study tips, and more. How can I assist you today?'
        });
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EduPathChatbot;
}
