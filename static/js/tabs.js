/**
 * AI Recruiting Demo - Tab Switching
 * Story 10.1: Tab Navigation
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Tabs.js loaded');
    
    // Get all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabButtons.length === 0) {
        console.warn('No tab buttons found');
        return;
    }
    
    console.log(`Found ${tabButtons.length} tabs`);
    
    // Add click event to each tab button
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            console.log(`Switching to tab: ${targetTab}`);
            
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Remove active class from all content
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Add active class to corresponding content
            const targetContent = document.getElementById(`tab-${targetTab}`);
            if (targetContent) {
                targetContent.classList.add('active');
                console.log(`Tab switched successfully: ${targetTab}`);
            } else {
                console.error(`Tab content not found: tab-${targetTab}`);
            }
        });
    });
    
    console.log('Tab switching initialized');
});

