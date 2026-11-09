window.alert("your attention is being monitored through your camera")


// Event listeners for menu buttons
document.getElementById('generate-notes').addEventListener('click', () => {
    toggleContent('notes-content');
    adjustLayout(3 / 5, 2 / 5);
  });
  
  document.getElementById('generate-flowchart').addEventListener('click', () => {
    toggleContent('flowchart-content');
    adjustLayout(3 / 5, 2 / 5);
  });
  
  document.getElementById('generate-summary').addEventListener('click', () => {
    toggleContent('summary-content');
    adjustLayout(3 / 5, 2 / 5);
  });
  
  // Function to show selected content
  function toggleContent(contentId) {
    const allContents = document.querySelectorAll('.content-item');
    allContents.forEach(content => {
      content.classList.remove('active'); // Hide all content
    });
  
    const selectedContent = document.getElementById(contentId);
    selectedContent.classList.add('active'); // Show selected content
  
    // Show the content section and make space for it
    const contentSection = document.getElementById('content-section');
    contentSection.style.width = "40%"; // Make content section 2/5 of the width
  }
  
  // Function to adjust layout when a button is clicked
  function adjustLayout(videoRatio, contentRatio) {
    const videoSection = document.getElementById('video-section');
    const contentSection = document.getElementById('content-section');
  
    // Adjust the width of the video and content sections
    videoSection.style.flex = videoRatio;
    contentSection.style.flex = contentRatio;
  }
  
  // Close content and return to initial layout
  function closeContent() {
    const allContents = document.querySelectorAll('.content-item');
    allContents.forEach(content => {
      content.classList.remove('active');
    });
  
    // Reset layout to initial state
    const contentSection = document.getElementById('content-section');
    contentSection.style.width = "0%"; // Hide content section
    const videoSection = document.getElementById('video-section');
    videoSection.style.flex = "300"; // Video takes full width again
  }
  