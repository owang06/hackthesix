// DOM elements
const uploadArea = document.getElementById('uploadArea');
const videoInput = document.getElementById('videoInput');
const uploadBtn = document.getElementById('uploadBtn');
const videoPreview = document.getElementById('videoPreview');
const previewVideo = document.getElementById('previewVideo');
const uploadVideoBtn = document.getElementById('uploadVideoBtn');
const changeVideoBtn = document.getElementById('changeVideoBtn');
const newUploadBtn = document.getElementById('newUploadBtn');
const uploadStatus = document.getElementById('uploadStatus');

// Debug: Check if elements are found
// DOM elements found successfully

// Store the selected file globally
let selectedFile = null;
let videoPreviewURL = null; // Store the video preview URL globally
let videoDataURL = null; // Store video as data URL for persistence
let uploadInProgress = false;
let uploadCompleted = false;
let tempFileInput = null; // Store the temporary file input

// Function to create and trigger file input
function createAndTriggerFileInput() {
  // Remove any existing temp file input
  if (tempFileInput && document.body.contains(tempFileInput)) {
    document.body.removeChild(tempFileInput);
  }
  
  // Create new file input
  tempFileInput = document.createElement('input');
  tempFileInput.type = 'file';
  tempFileInput.accept = 'video/*';
  tempFileInput.style.display = 'none';
  
  tempFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      handleVideoSelection(file);
    }
    
    // Reset the temp file input for next use
    tempFileInput.value = '';
  });
  
  // Handle when user cancels the file picker
  tempFileInput.addEventListener('cancel', () => {
    // Reset for next use
    tempFileInput.value = '';
  });
  
  document.body.appendChild(tempFileInput);
  tempFileInput.click();
}

// Event listeners
uploadBtn.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  createAndTriggerFileInput();
});
uploadArea.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  videoInput.click();
});



// Drag and drop functionality
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
  uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  
  const files = e.dataTransfer.files;
  if (files.length > 0 && files[0].type.startsWith('video/')) {
    handleVideoSelection(files[0]);
  }
});

// File input change
videoInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    handleVideoSelection(file);
  }
});



// Handle video selection
function handleVideoSelection(file) {
  // Create preview URL
  const videoURL = URL.createObjectURL(file);
  previewVideo.src = videoURL;
  
  // Show preview and hide upload area
  uploadArea.style.display = 'none';
  videoPreview.style.display = 'block';
  
  // Store the file and URL globally
  selectedFile = file;
  videoPreviewURL = videoURL;
  
  // Store the video URL for later use
  previewVideo.dataset.videoUrl = videoURL;
  
  // Also create a data URL as backup and store in localStorage
  const reader = new FileReader();
  reader.onload = function(e) {
    videoDataURL = e.target.result;
    // Store in localStorage for persistence across reloads
    localStorage.setItem('videoDataURL', videoDataURL);
    localStorage.setItem('videoFileName', file.name);
    localStorage.setItem('uploadCompleted', 'false');
  };
  reader.readAsDataURL(file);
  
  // Update status
  updateStatus('Video selected: ' + file.name, 'success');
}

// Change video button
changeVideoBtn.addEventListener('click', () => {
  resetUploadState();
});

// New upload button
newUploadBtn.addEventListener('click', () => {
  resetUploadState();
});

// Reset upload state function
function resetUploadState() {
  // Reset everything
  videoInput.value = '';
  previewVideo.src = '';
  selectedFile = null;
  videoPreviewURL = null;
  videoDataURL = null;
  
  // Reset upload flags
  uploadInProgress = false;
  uploadCompleted = false;
  
  // Reset button state
  uploadVideoBtn.disabled = false;
  uploadVideoBtn.style.cursor = 'pointer';
  
  // Clear localStorage
  localStorage.removeItem('videoDataURL');
  localStorage.removeItem('videoFileName');
  localStorage.removeItem('uploadCompleted');
  localStorage.removeItem('videoId');
  localStorage.removeItem('uploadStartTime');
  
  // Show upload area and hide preview
  uploadArea.style.display = 'block';
  videoPreview.style.display = 'none';
  
  // Reset button states
  uploadVideoBtn.textContent = 'Upload & Analyze';
  uploadVideoBtn.disabled = false;
  uploadVideoBtn.style.background = '#0071e3';
  newUploadBtn.style.display = 'none';
  
  // Clear status
  updateStatus('');
}

// Upload video button
console.log('Setting up upload button event listener');
if (uploadVideoBtn) {
  console.log('Upload button found, adding event listener');
  console.log('Button disabled:', uploadVideoBtn.disabled);
  console.log('Button style:', uploadVideoBtn.style.cssText);
  console.log('Button parent display:', videoPreview.style.display);
  console.log('Button offsetParent:', uploadVideoBtn.offsetParent);
  
    uploadVideoBtn.addEventListener('click', async function(e) {
    // Prevent double clicks
    e.preventDefault();
    e.stopPropagation();
  
  // Check if upload is already in progress
  if (uploadInProgress) {
    console.log('Upload already in progress, ignoring click');
    return;
  }
  
  // Check if file is selected
  if (!selectedFile) {
    console.log('No file selected');
    updateStatus('No video selected', 'error');
    return;
  }
  
  console.log('=== UPLOAD STARTED ===');
  uploadInProgress = true;
  localStorage.setItem('uploadStartTime', Date.now().toString());
  
  if (!selectedFile) {
    updateStatus('No video selected', 'error');
    uploadInProgress = false;
    return;
  }
  
  // Additional validation
  if (!(selectedFile instanceof File)) {
    updateStatus('Invalid file object', 'error');
    uploadInProgress = false;
    return;
  }
  
  // Store current video state before upload
  const currentVideoSrc = previewVideo.src;
  console.log('Before upload - Video src:', currentVideoSrc);
  console.log('Before upload - Global video URL:', videoPreviewURL);
  
  updateStatus('Uploading video...', '');
  uploadVideoBtn.disabled = true;
  uploadVideoBtn.textContent = 'Uploading...';
  uploadVideoBtn.style.cursor = 'not-allowed';
  
  try {
    const formData = new FormData();
    formData.append('video', selectedFile);
    
    // Debug: Log the file being sent
    console.log('Sending file:', selectedFile.name, selectedFile.type, selectedFile.size);
    console.log('File object:', selectedFile);
    console.log('FormData entries:');
    for (let [key, value] of formData.entries()) {
      console.log(key, value, typeof value);
    }
    
    const response = await fetch('http://127.0.0.1:5000/upload', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let the browser set it automatically for FormData
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('=== UPLOAD SUCCESS ===');
      uploadInProgress = false;
      
      // Store video ID for status polling
      const videoId = result.video_id;
      localStorage.setItem('videoId', videoId);
      
      updateStatus('Upload successful! Processing started...', 'success');
      uploadVideoBtn.textContent = 'Processing...';
      uploadVideoBtn.disabled = true;
      uploadVideoBtn.style.background = '#ff9500'; // Orange color for processing
      
      // Start polling for status updates
      pollProcessingStatus(videoId);
      
      // Debug: Check if preview is still visible
      console.log('Preview display:', videoPreview.style.display);
      console.log('Upload area display:', uploadArea.style.display);
      console.log('Video src:', previewVideo.src);
      
      // Ensure preview stays visible and video is loaded
      videoPreview.style.display = 'block';
      uploadArea.style.display = 'none';
      
      // Check if video element is still valid
      console.log('Video element exists:', !!previewVideo);
      console.log('Video element readyState:', previewVideo.readyState);
      
      // Force restore video and ensure it's visible
      if (videoPreviewURL) {
        previewVideo.src = videoPreviewURL;
        console.log('Forced video src restoration:', videoPreviewURL);
        
        // Ensure video loads
        previewVideo.load();
      } else if (videoDataURL) {
        // Fallback to data URL if blob URL is lost
        previewVideo.src = videoDataURL;
        console.log('Fallback to data URL restoration:', videoDataURL.substring(0, 50) + '...');
        previewVideo.load();
      }
      
      console.log('After upload - Video src:', previewVideo.src);
      console.log('After upload - Global video URL:', videoPreviewURL);
      console.log('After upload - Video element display:', videoPreview.style.display);
      console.log('=== UPLOAD COMPLETE ===');
      
      // Add a delay to see if something happens after this
      setTimeout(() => {
        console.log('=== 2 SECONDS AFTER UPLOAD ===');
        console.log('Video still exists:', !!previewVideo);
        console.log('Video src still there:', previewVideo.src);
        console.log('Upload completed flag:', uploadCompleted);
      }, 2000);
      
      // Also add a longer check to ensure video stays
      setTimeout(() => {
        console.log('=== 5 SECONDS AFTER UPLOAD ===');
        if (videoPreviewURL && previewVideo.src !== videoPreviewURL) {
          console.log('Restoring video after 5 seconds');
          previewVideo.src = videoPreviewURL;
          previewVideo.load();
        }
      }, 5000);
    } else {
      uploadInProgress = false;
      updateStatus('Upload failed: ' + (result.error || response.statusText), 'error');
      uploadVideoBtn.disabled = false;
      uploadVideoBtn.textContent = 'Upload & Analyze';
      uploadVideoBtn.style.background = '#0071e3'; // Reset to original color
      uploadVideoBtn.style.cursor = 'pointer';
    }
  } catch (err) {
    console.log('=== UPLOAD ERROR ===');
    console.error('Upload error:', err);
    uploadInProgress = false;
    updateStatus('Upload error: ' + err.message, 'error');
    uploadVideoBtn.disabled = false;
    uploadVideoBtn.textContent = 'Upload & Analyze';
    uploadVideoBtn.style.background = '#0071e3'; // Reset to original color
    uploadVideoBtn.style.cursor = 'pointer';
  }
  });
}

// Poll processing status
async function pollProcessingStatus(videoId) {
  const maxAttempts = 60; // 5 minutes max (60 * 5 seconds)
  let attempts = 0;
  
  const poll = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/status/${videoId}`);
      const status = await response.json();
      
      if (response.ok) {
        console.log('Status update:', status);
        
        // Update status message
        updateStatus(status.message, status.status === 'error' ? 'error' : 'success');
        
        // Update progress if available
        if (status.progress !== undefined) {
          uploadVideoBtn.textContent = `Processing... ${status.progress}%`;
        }
        
        if (status.status === 'completed') {
          // Processing is complete
          uploadCompleted = true;
          localStorage.setItem('uploadCompleted', 'true');
          
          uploadVideoBtn.textContent = 'Processing Complete';
          uploadVideoBtn.style.background = '#28a745'; // Green color for success
          newUploadBtn.style.display = 'inline-block'; // Show new upload button
          
          updateStatus('Processing completed successfully!', 'success');
          
          // Show results if available
          if (status.results) {
            console.log('Processing results:', status.results);
            updateStatus(`Processing completed! Extracted ${status.results.frames_extracted} frames.`, 'success');
          }
          
          return; // Stop polling
        } else if (status.status === 'error') {
          // Processing failed
          uploadVideoBtn.textContent = 'Processing Failed';
          uploadVideoBtn.style.background = '#dc3545'; // Red color for error
          uploadVideoBtn.disabled = false;
          return; // Stop polling
        }
      } else {
        console.error('Failed to get status:', status);
      }
    } catch (error) {
      console.error('Error polling status:', error);
    }
    
    // Continue polling if not complete
    attempts++;
    if (attempts < maxAttempts) {
      setTimeout(poll, 5000); // Poll every 5 seconds
    } else {
      // Timeout
      updateStatus('Processing timeout - please try again', 'error');
      uploadVideoBtn.textContent = 'Processing Timeout';
      uploadVideoBtn.style.background = '#dc3545';
      uploadVideoBtn.disabled = false;
    }
  };
  
  // Start polling
  poll();
}

// Update status message
function updateStatus(message, type = '') {
  uploadStatus.textContent = message;
  uploadStatus.className = 'upload-status';
  if (type) {
    uploadStatus.classList.add(type);
  }
}

// Removed auto-reset to avoid conflicts

// Test function to check button
window.testButton = function() {
  console.log('Testing button click...');
  if (uploadVideoBtn) {
    console.log('Button exists, trying to click programmatically');
    console.log('Button visible:', uploadVideoBtn.offsetParent !== null);
    console.log('Button parent visible:', videoPreview.style.display);
    uploadVideoBtn.click();
  } else {
    console.log('Button not found');
  }
};

// Test function to show the video preview
window.showPreview = function() {
  console.log('Showing video preview...');
  uploadArea.style.display = 'none';
  videoPreview.style.display = 'block';
  console.log('Video preview display:', videoPreview.style.display);
};

// Fade-in animation for hero section
window.addEventListener('DOMContentLoaded', () => {
  console.log('=== PAGE LOADED ===');
  
  // Check if we have a video stored in localStorage
  const storedVideoDataURL = localStorage.getItem('videoDataURL');
  const storedUploadCompleted = localStorage.getItem('uploadCompleted');
  const storedVideoId = localStorage.getItem('videoId');
  const storedFileName = localStorage.getItem('videoFileName');
  
  if (storedVideoDataURL) {
    console.log('Found stored video, restoring preview');
    
    // Restore video preview
    previewVideo.src = storedVideoDataURL;
    videoDataURL = storedVideoDataURL;
    
    // Show preview and hide upload area
    uploadArea.style.display = 'none';
    videoPreview.style.display = 'block';
    
    // Update status based on upload completion
    if (storedUploadCompleted === 'true') {
      uploadCompleted = true;
      updateStatus('Upload completed! Video ID: ' + storedVideoId, 'success');
      uploadVideoBtn.textContent = 'Processing Complete';
      uploadVideoBtn.disabled = true;
      uploadVideoBtn.style.background = '#28a745';
      newUploadBtn.style.display = 'inline-block';
    } else if (storedVideoId) {
      // If we have a video ID but no completion status, check if processing is still ongoing
      updateStatus('Video selected: ' + storedFileName + ' - Checking processing status...', 'success');
      pollProcessingStatus(storedVideoId);
    } else {
      updateStatus('Video selected: ' + storedFileName, 'success');
    }
  }
  
  // Clear localStorage when page is unloaded/closed (simplified to avoid violations)
  window.addEventListener('beforeunload', (e) => {
    // Don't prevent unload, just clear storage
    localStorage.removeItem('videoDataURL');
    localStorage.removeItem('videoFileName');
    localStorage.removeItem('uploadCompleted');
    localStorage.removeItem('videoId');
    localStorage.removeItem('uploadStartTime');
  });
  
  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && uploadCompleted) {
      console.log('Page became visible again - ensuring video is still there');
      // Ensure video is still visible
      if (videoPreviewURL && previewVideo.src !== videoPreviewURL) {
        previewVideo.src = videoPreviewURL;
        previewVideo.load();
      }
    }
  });
  
  const hero = document.querySelector('.hero');
  hero.style.opacity = 0;
  hero.style.transform = 'translateY(40px)';
  setTimeout(() => {
    hero.style.transition = 'opacity 1s cubic-bezier(.4,0,.2,1), transform 1s cubic-bezier(.4,0,.2,1)';
    hero.style.opacity = 1;
    hero.style.transform = 'translateY(0)';
  }, 100);
});

// Check for page unload/reload
window.addEventListener('beforeunload', () => {
  console.log('=== PAGE UNLOADING ===');
});

// Check for page visibility changes
document.addEventListener('visibilitychange', () => {
  console.log('=== VISIBILITY CHANGE ===', document.visibilityState);
});

// Prevent page unload during and after upload
// Variables already declared at the top

// Remove the duplicate beforeunload listener since we moved it to DOMContentLoaded

// Only prevent form submissions if they're not our upload
document.addEventListener('submit', (e) => {
  // Only prevent if it's not our video upload
  if (!e.target.closest('.upload-container')) {
    console.log('=== FORM SUBMIT PREVENTED ===');
    e.preventDefault();
    e.stopPropagation();
    return false;
  }
}); 