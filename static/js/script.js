// DOM elements
        const startCameraBtn = document.getElementById('startCamera');
        const stopCameraBtn = document.getElementById('stopCamera');
        const captureBtn = document.getElementById('captureBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        const fileInput = document.getElementById('fileInput');
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const previewImg = document.getElementById('previewImg');
        const statusDiv = document.getElementById('status');
        const videoOverlay = document.getElementById('videoOverlay');
        const imageContainer = document.getElementById('imageContainer');
        
        // Multi-model result containers
        const generalSection = document.getElementById('generalSection');
        const pepperSection = document.getElementById('pepperSection');
        const generalObjects = document.getElementById('generalObjects');
        const bellPeppers = document.getElementById('bellPeppers');
        const objectCount = document.getElementById('objectCount');
        const pepperCount = document.getElementById('pepperCount');
        const processingTime = document.getElementById('processingTime');

        let stream = null;
        let processingStartTime = null;

        // Accessibility and keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Space bar to capture when camera is active
            if (e.code === 'Space' && !captureBtn.disabled && !e.target.matches('input, textarea')) {
                e.preventDefault();
                captureBtn.click();
            }
            
            // Enter key to upload when file is selected
            if (e.code === 'Enter' && !uploadBtn.disabled && e.target === fileInput) {
                e.preventDefault();
                uploadBtn.click();
            }
            
            // Escape key to stop camera
            if (e.code === 'Escape' && !stopCameraBtn.disabled) {
                e.preventDefault();
                stopCameraBtn.click();
            }
        });

        // Focus management for better accessibility
        function manageFocus() {
            const focusableElements = document.querySelectorAll(
                'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );
            
            focusableElements.forEach((element, index) => {
                element.addEventListener('keydown', (e) => {
                    if (e.code === 'Tab') {
                        const nextIndex = e.shiftKey ? index - 1 : index + 1;
                        if (nextIndex >= 0 && nextIndex < focusableElements.length) {
                            e.preventDefault();
                            focusableElements[nextIndex].focus();
                        }
                    }
                });
            });
        }

        // Initialize focus management
        manageFocus();

        // Create dynamic particles
        function createParticles() {
            const particleContainer = document.createElement('div');
            particleContainer.className = 'particle-container';
            particleContainer.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
                overflow: hidden;
            `;
            document.body.appendChild(particleContainer);

            for (let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.cssText = `
                    left: ${Math.random() * 100}%;
                    animation-delay: ${Math.random() * 15}s;
                    animation-duration: ${15 + Math.random() * 10}s;
                `;
                particleContainer.appendChild(particle);
            }
        }

        // Initialize particles
        createParticles();

        // Add dynamic card animations
        function enhanceCardAnimations() {
            const cards = document.querySelectorAll('.card');
            
            cards.forEach(card => {
                card.addEventListener('mouseenter', () => {
                    // Add subtle glow effect
                    card.style.boxShadow = '0 25px 50px -12px rgba(99, 102, 241, 0.25)';
                });
                
                card.addEventListener('mouseleave', () => {
                    card.style.boxShadow = '';
                });
            });
        }

        // Initialize card animations
        enhanceCardAnimations();

        // Add visual feedback for interactions
        function addVisualFeedback(element, type = 'success') {
            const originalClass = element.className;
            element.classList.add(type === 'success' ? 'btn-success' : 'btn-danger');
            setTimeout(() => {
                element.className = originalClass;
            }, 200);
        }

        // Enhanced error handling with user-friendly messages
        function handleError(error, context = '') {
            console.error(`Error in ${context}:`, error);
            
            let userMessage = 'An unexpected error occurred. Please try again.';
            
            if (error.name === 'NotAllowedError') {
                userMessage = 'Camera access denied. Please allow camera permissions and try again.';
            } else if (error.name === 'NotFoundError') {
                userMessage = 'No camera found. Please connect a camera and try again.';
            } else if (error.name === 'NotReadableError') {
                userMessage = 'Camera is already in use by another application.';
            } else if (error.message.includes('Network')) {
                userMessage = 'Network error. Please check your connection and try again.';
            } else if (error.message.includes('Server error')) {
                userMessage = 'Server is temporarily unavailable. Please try again later.';
            }
            
            updateStatus(userMessage, 'error');
        }

        // Add loading states to buttons
        function setButtonLoading(button, isLoading) {
            if (isLoading) {
                button.disabled = true;
                button.dataset.originalText = button.innerHTML;
                button.innerHTML = '<div class="loading"></div> Processing...';
            } else {
                button.disabled = false;
                if (button.dataset.originalText) {
                    button.innerHTML = button.dataset.originalText;
                    delete button.dataset.originalText;
                }
            }
        }

        // Utility functions
        function updateStatus(message, type = 'info', showLoading = false) {
            statusDiv.className = type;
            if (showLoading) {
                statusDiv.innerHTML = `<div class="loading"></div> ${message}`;
            } else {
                statusDiv.innerHTML = `<i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i> ${message}`;
            }
        }

        function showImageContainer() {
            imageContainer.style.display = 'block';
            imageContainer.classList.add('fade-in');
        }

        function showDetectionsSection() {
            detectionsSection.style.display = 'block';
            detectionsSection.classList.add('fade-in');
        }

        function hideResults() {
            imageContainer.style.display = 'none';
            generalSection.style.display = 'none';
            pepperSection.style.display = 'none';
            imageContainer.classList.remove('fade-in');
        }
        
        function displayGeneralObjects(objects) {
            if (!objects || objects.length === 0) {
                generalSection.style.display = 'none';
                return;
            }
            
            generalSection.style.display = 'block';
            
            let html = '';
            objects.forEach((obj, index) => {
                if (obj.confidence > 0.3) {
                    const confidencePercent = Math.round(obj.confidence * 100);
                    html += `
                    <div class="detection-item" style="animation-delay: ${index * 0.1}s">
                        <div class="detection-info">
                            <div class="detection-class">${obj.class_name}</div>
                            <div class="detection-confidence">${confidencePercent}% confidence</div>
                            <div class="confidence-bar">
                                <div class="confidence-level" style="width: ${confidencePercent}%"></div>
                            </div>
                        </div>
                        <div class="detection-id">ID: ${obj.class_id}</div>
                    </div>`;
                }
            });
            
            if (html === '') {
                html = '<div class="no-detections"><i class="fas fa-search"></i><span>No general objects detected with sufficient confidence</span></div>';
            }
            
            generalObjects.innerHTML = html;
        }
        
        // Function to convert numeric quality values to human-readable descriptions
        function getQualityDescription(value) {
            if (value >= 90) return 'Excellent';
            if (value >= 75) return 'Good';
            if (value >= 60) return 'Fair';
            if (value >= 40) return 'Poor';
            return 'Very Poor';
        }
        
        // Function to get color-coded CSS class for quality values
        function getQualityClass(value) {
            if (value >= 90) return 'quality-excellent';
            if (value >= 75) return 'quality-good';
            if (value >= 60) return 'quality-fair';
            if (value >= 40) return 'quality-poor';
            return 'quality-very-poor';
        }
        
        function displayBellPeppers(peppers) {
            if (!peppers || peppers.length === 0) {
                pepperSection.style.display = 'none';
                return;
            }
            
            pepperSection.style.display = 'block';
            
            let html = '';
            peppers.forEach((pepper, index) => {
                const confidencePercent = Math.round(pepper.confidence * 100);
                
                // Build pepper analysis components
                let qualityMetricsHTML = '';
                let recommendationsHTML = '';
                let qualityScoreHTML = '';
                
                if (pepper.quality_analysis) {
                    const qa = pepper.quality_analysis;
                    const qualityClass = `quality-${qa.quality_category.toLowerCase()}`;
                    
                    qualityScoreHTML = `
                        <div class="quality-score ${qualityClass}">
                            ${qa.quality_category} (${Math.round(qa.quality_score)}/100)
                        </div>
                    `;
                    
                    qualityMetricsHTML = `
                        <div class="quality-metrics">
                            <div class="metric-card">
                                <div class="metric-value ${getQualityClass(qa.color_uniformity)}">${getQualityDescription(qa.color_uniformity)}</div>
                                <div class="metric-label">Color Uniformity</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value ${getQualityClass(qa.size_consistency)}">${getQualityDescription(qa.size_consistency)}</div>
                                <div class="metric-label">Size Consistency</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value ${getQualityClass(qa.surface_quality)}">${getQualityDescription(qa.surface_quality)}</div>
                                <div class="metric-label">Surface Quality</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value ${getQualityClass(qa.ripeness_level)}">${getQualityDescription(qa.ripeness_level)}</div>
                                <div class="metric-label">Ripeness Level</div>
                            </div>
                        </div>
                    `;
                    
                    // Add recommendations if available
                    if (qa.recommendations && qa.recommendations.length > 0) {
                        recommendationsHTML = `
                            <div class="recommendations">
                                <h4><i class="fas fa-lightbulb"></i> Recommendations</h4>
                                <ul>
                                    ${qa.recommendations.map(rec => {
                                        // Check if recommendation is disease-related or warning
                                        const isWarning = rec.toLowerCase().includes('disease') || 
                                                        rec.toLowerCase().includes('treatment') || 
                                                        rec.toLowerCase().includes('poor') || 
                                                        rec.toLowerCase().includes('damage') ||
                                                        rec.toLowerCase().includes('infection');
                                        return `<li class="${isWarning ? 'disease-warning' : ''}">${rec}</li>`;
                                    }).join('')}
                                </ul>
                            </div>
                        `;
                    }
                }
                
                // Advanced AI Analysis HTML  
                let advancedAnalysisHTML = '';
                let ripenessAnalysisHTML = '';
                let nutritionAnalysisHTML = '';
                
                // Ripeness Prediction Analysis
                if (pepper.ripeness_prediction) {
                    const ripeness = pepper.ripeness_prediction;
                    const stageClass = ripeness.current_stage.toLowerCase().replace(' ', '-');
                    
                    ripenessAnalysisHTML = `
                        <div class="ripeness-analysis">
                            <div class="analysis-header">
                                <h4><i class="fas fa-clock"></i> Ripeness Prediction</h4>
                            </div>
                            <div class="ripeness-info">
                                <div class="ripeness-stage ${stageClass}">
                                    <span class="stage-name">${ripeness.current_stage}</span>
                                    <span class="ripeness-percent">${ripeness.ripeness_percentage}%</span>
                                </div>
                                <div class="harvest-timing">
                                    <i class="fas fa-calendar"></i>
                                    <span>${ripeness.harvest_recommendation}</span>
                                </div>
                                ${ripeness.days_to_optimal_harvest > 0 ? 
                                    `<div class="days-to-optimal">
                                        <i class="fas fa-hourglass-half"></i>
                                        <span>${ripeness.days_to_optimal_harvest} days to optimal harvest</span>
                                    </div>` : ''
                                }
                            </div>
                        </div>
                    `;
                }
                
                // Nutritional Analysis  
                if (pepper.nutrition) {
                    const nutrition = pepper.nutrition;
                    const highlights = nutrition.nutritional_highlights || [];
                    
                    nutritionAnalysisHTML = `
                        <div class="nutrition-analysis">
                            <div class="analysis-header">
                                <h4><i class="fas fa-apple-alt"></i> Nutritional Analysis</h4>
                            </div>
                            <div class="nutrition-content">
                                <div class="nutrition-stats">
                                    <div class="nutrition-item">
                                        <span class="nutrition-label">Vitamin C</span>
                                        <span class="nutrition-value">${Math.round(nutrition.per_pepper.vitamin_c)}mg</span>
                                    </div>
                                    <div class="nutrition-item">
                                        <span class="nutrition-label">Weight</span>
                                        <span class="nutrition-value">${nutrition.estimated_weight_g}g</span>
                                    </div>
                                    <div class="nutrition-item">
                                        <span class="nutrition-label">Calories</span>
                                        <span class="nutrition-value">${Math.round(nutrition.per_pepper.calories)}</span>
                                    </div>
                                </div>
                                ${highlights.length > 0 ? 
                                    `<div class="nutrition-highlights">
                                        ${highlights.map(h => `<span class="highlight-badge">${h}</span>`).join('')}
                                    </div>` : ''
                                }
                            </div>
                        </div>
                    `;
                }
                
                // Shelf Life Analysis
                let shelfLifeHTML = '';
                if (pepper.shelf_life) {
                    const shelfLife = pepper.shelf_life;
                    
                    shelfLifeHTML = `
                        <div class="shelf-life-analysis">
                            <div class="analysis-header">
                                <h4><i class="fas fa-box"></i> Shelf Life Estimation</h4>
                            </div>
                            <div class="shelf-life-options">
                                <div class="storage-option">
                                    <i class="fas fa-home"></i>
                                    <span class="storage-type">Room Temperature</span>
                                    <span class="storage-duration">${shelfLife.room_temperature.days} days</span>
                                </div>
                                <div class="storage-option">
                                    <i class="fas fa-snowflake"></i>
                                    <span class="storage-type">Refrigerated</span>
                                    <span class="storage-duration">${shelfLife.refrigerated.days} days</span>
                                </div>
                                <div class="storage-option best">
                                    <i class="fas fa-star"></i>
                                    <span class="storage-type">Optimal Storage</span>
                                    <span class="storage-duration">${shelfLife.optimal_storage.days} days</span>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // Market Analysis
                let marketAnalysisHTML = '';
                if (pepper.market_analysis) {
                    const market = pepper.market_analysis;
                    const gradeClass = market.grade.toLowerCase().replace(' ', '-');
                    
                    marketAnalysisHTML = `
                        <div class="market-analysis">
                            <div class="analysis-header">
                                <h4><i class="fas fa-chart-line"></i> Market Analysis</h4>
                            </div>
                            <div class="market-content">
                                <div class="market-grade ${gradeClass}">
                                    <span class="grade-name">${market.grade}</span>
                                    <span class="grade-description">${market.grade_description}</span>
                                </div>
                                <div class="market-price">
                                    <i class="fas fa-dollar-sign"></i>
                                    <span>$${market.estimated_price_per_kg}/kg</span>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // Combine all advanced analyses
                if (ripenessAnalysisHTML || nutritionAnalysisHTML || shelfLifeHTML || marketAnalysisHTML) {
                    advancedAnalysisHTML = `
                        <div class="advanced-analysis-container">
                            <div class="advanced-analysis-header">
                                <h3><i class="fas fa-brain"></i> Advanced AI Analysis</h3>
                            </div>
                            <div class="advanced-analysis-grid">
                                ${ripenessAnalysisHTML}
                                ${nutritionAnalysisHTML}
                                ${shelfLifeHTML}
                                ${marketAnalysisHTML}
                            </div>
                        </div>
                    `;
                }
                
                // Disease analysis HTML
                let diseaseAnalysisHTML = '';
                let healthStatusHTML = '';
                
                if (pepper.disease_analysis && !pepper.disease_analysis.error) {
                    const disease = pepper.disease_analysis;
                    const isHealthy = disease.is_healthy;
                    const diseaseClass = isHealthy ? 'healthy' : 'diseased';
                    
                    diseaseAnalysisHTML = `
                        <div class="disease-analysis">
                            <div class="disease-header">
                                <h4><i class="fas fa-microscope"></i> Disease Analysis</h4>
                            </div>
                            <div class="disease-result ${diseaseClass}">
                                <div class="disease-info">
                                    <span class="disease-name">${disease.disease}</span>
                                    <span class="disease-confidence">${Math.round(disease.confidence * 100)}% confidence</span>
                                </div>
                                ${disease.severity ? `<span class="disease-severity severity-${disease.severity.toLowerCase().replace(' ', '-')}">${disease.severity} Risk</span>` : ''}
                            </div>
                            ${disease.description ? `<p class="disease-description">${disease.description}</p>` : ''}
                            ${disease.treatment && !isHealthy ? `<div class="disease-treatment"><strong>Treatment:</strong> <span class="disease-warning">${disease.treatment}</span></div>` : ''}
                        </div>
                    `;
                }
                
                // Health status HTML
                if (pepper.health_status) {
                    const healthScore = pepper.overall_health_score || 0;
                    const healthClass = healthScore >= 80 ? 'excellent' : healthScore >= 60 ? 'good' : healthScore >= 40 ? 'fair' : 'poor';
                    
                    healthStatusHTML = `
                        <div class="health-status ${healthClass}">
                            <div class="health-score">
                                <span class="health-value">${Math.round(healthScore)}</span>
                                <span class="health-label">Health Score</span>
                            </div>
                            <span class="health-status-text">${pepper.health_status}</span>
                        </div>
                    `;
                }
                
                html += `
                <div class="detection-item pepper-item" style="animation-delay: ${index * 0.1}s">
                    <div class="pepper-header">
                        ${pepper.crop_url ? `<img src="${pepper.crop_url}?t=${Date.now()}" alt="Bell Pepper ${pepper.pepper_id}" class="pepper-crop-image">` : ''}
                        <div class="pepper-info">
                            <div class="pepper-title">
                                <h3 class="pepper-name">
                                    <i class="fas fa-pepper-hot"></i>
                                    ${pepper.variety}
                                </h3>
                                <span class="pepper-id-badge">${pepper.pepper_id}</span>
                                ${qualityScoreHTML}
                            </div>
                            <div class="pepper-confidence">
                                ${confidencePercent}% detection confidence
                            </div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
                            </div>
                        </div>
                        ${healthStatusHTML}
                    </div>
                    ${qualityMetricsHTML}
                    ${advancedAnalysisHTML}
                    ${diseaseAnalysisHTML}
                    ${recommendationsHTML}
                </div>`;
            });
            
            bellPeppers.innerHTML = html;
        }

        // Event Listeners
        startCameraBtn.addEventListener('click', async () => {
            try {
                setButtonLoading(startCameraBtn, true);
                updateStatus('Starting camera...', 'info', true);
                
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'environment' }, 
                    audio: false 
                });
                
                video.srcObject = stream;
                videoOverlay.classList.add('hidden');
                captureBtn.disabled = false;
                stopCameraBtn.disabled = false;
                startCameraBtn.disabled = true;
                startCameraBtn.classList.remove('pulse');
                
                setButtonLoading(startCameraBtn, false);
                updateStatus('Camera active. Point at objects to detect.', 'success');
                addVisualFeedback(startCameraBtn, 'success');
            } catch (err) {
                setButtonLoading(startCameraBtn, false);
                handleError(err, 'camera initialization');
            }
        });

        stopCameraBtn.addEventListener('click', () => {
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
                video.srcObject = null;
                videoOverlay.classList.remove('hidden');
                stream = null;
                captureBtn.disabled = true;
                stopCameraBtn.disabled = true;
                startCameraBtn.disabled = false;
                startCameraBtn.classList.add('pulse');
                updateStatus('Camera stopped.', 'info');
            }
        });

        captureBtn.addEventListener('click', async () => {
            if (!stream) { 
                updateStatus('Please start the camera first.', 'error');
                return;
            }
            
            try {
                setButtonLoading(captureBtn, true);
                addVisualFeedback(captureBtn, 'success');
                
                const w = video.videoWidth;
                const h = video.videoHeight;
                canvas.width = w;
                canvas.height = h;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, w, h);
                
                canvas.toBlob(async (blob) => {
                    await uploadBlob(blob);
                    setButtonLoading(captureBtn, false);
                }, 'image/jpeg', 0.95);
            } catch (err) {
                setButtonLoading(captureBtn, false);
                handleError(err, 'image capture');
            }
        });

        fileInput.addEventListener('change', () => {
            uploadBtn.disabled = !fileInput.files[0];
            if (fileInput.files[0]) {
                updateStatus('File selected: ' + fileInput.files[0].name, 'success');
            }
        });

        uploadBtn.addEventListener('click', async () => {
            const file = fileInput.files[0];
            if (!file) { 
                updateStatus('Please select a file first.', 'error');
                return;
            }
            
            try {
                setButtonLoading(uploadBtn, true);
                addVisualFeedback(uploadBtn, 'success');
                await uploadFile(file);
                setButtonLoading(uploadBtn, false);
            } catch (err) {
                setButtonLoading(uploadBtn, false);
                handleError(err, 'file upload');
            }
        });

        // Drag and drop functionality
        const fileLabel = document.querySelector('.file-label');
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileLabel.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            fileLabel.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileLabel.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            fileLabel.style.borderColor = 'var(--primary)';
            fileLabel.style.backgroundColor = 'rgba(105, 108, 255, 0.05)';
        }

        function unhighlight() {
            fileLabel.style.borderColor = 'var(--gray)';
            fileLabel.style.backgroundColor = 'transparent';
        }

        fileLabel.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            uploadBtn.disabled = !files[0];
            if (files[0]) {
                updateStatus('File selected: ' + files[0].name, 'success');
            }
        }

        // Upload functions
        async function uploadBlob(blob) {
            const fd = new FormData();
            fd.append('image', blob, 'capture.jpg');
            await sendForm(fd);
        }

        async function uploadFile(file) {
            const fd = new FormData();
            fd.append('image', file);
            await sendForm(fd);
        }

        async function sendForm(fd) {
            processingStartTime = Date.now();
            updateStatus('Processing image...', 'info', true);
            hideResults();
            
            try {
                const resp = await fetch('/upload', { method: 'POST', body: fd });
                const data = await resp.json();
                
                if (!resp.ok) {
                    throw new Error(data.error || `Server error: ${resp.status}`);
                }
                
                // Calculate processing time
                const processingTimeMs = Date.now() - processingStartTime;
                
                // Show annotated image with proper container sizing
                previewImg.src = data.result_url + '?t=' + Date.now();
                
                // Determine image orientation and apply appropriate container class
                previewImg.onload = function() {
                    const imageContainer = document.getElementById('imageContainer');
                    imageContainer.classList.remove('landscape', 'portrait');
                    
                    if (this.naturalWidth > this.naturalHeight) {
                        imageContainer.classList.add('landscape');
                    } else {
                        imageContainer.classList.add('portrait');
                    }
                };
                
                showImageContainer();
                
                // Update processing time
                processingTime.textContent = processingTimeMs + 'ms';
                
                // Update counters
                objectCount.textContent = data.summary.total_objects || 0;
                pepperCount.textContent = data.summary.bell_peppers_found || 0;
                
                // Count healthy peppers
                const healthyCount = data.bell_peppers.filter(pepper => {
                    if (pepper.disease_analysis && pepper.disease_analysis.is_healthy) {
                        return true;
                    }
                    // Fallback to health score if disease analysis not available
                    return pepper.overall_health_score >= 70;
                }).length;
                
                const healthyCountElement = document.getElementById('healthyCount');
                if (healthyCountElement) {
                    healthyCountElement.textContent = healthyCount;
                }
                
                // Display results from different models
                displayGeneralObjects(data.general_objects);
                displayBellPeppers(data.bell_peppers);
                
                // Update status with summary
                let statusMessage = data.message || 'Analysis complete';
                if (data.summary.bell_peppers_found > 0) {
                    const avgQuality = Math.round(data.summary.avg_quality_score || 0);
                    statusMessage += ` | Avg Quality: ${avgQuality}/100`;
                }
                
                updateStatus(statusMessage, 'success');
            } catch (err) {
                handleError(err, 'image processing');
            }
        }

