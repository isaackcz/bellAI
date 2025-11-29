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
        
        // Offline functionality
        let isOnline = navigator.onLine;
        let queuedUploadsCount = 0;
        
        // Initialize offline storage
        let offlineStorageReady = false;
        if (typeof window.offlineStorage !== 'undefined') {
            window.offlineStorage.init().then(() => {
                offlineStorageReady = true;
                updateQueuedUploadsCount();
                console.log('✅ Offline storage initialized');
            }).catch(err => {
                console.error('❌ Failed to initialize offline storage:', err);
            });
        }
        
        // Monitor online/offline status
        window.addEventListener('online', () => {
            isOnline = true;
            updateConnectionStatus();
            processQueuedUploads();
        });
        
        window.addEventListener('offline', () => {
            isOnline = false;
            updateConnectionStatus();
        });
        
        // Listen for service worker messages
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.addEventListener('message', (event) => {
                if (event.data.type === 'UPLOAD_OFFLINE') {
                    handleOfflineUpload();
                } else if (event.data.type === 'UPLOAD_SUCCESS') {
                    updateQueuedUploadsCount();
                } else if (event.data.type === 'SYNC_UPLOADS') {
                    processQueuedUploads();
                }
            });
        }

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
                    card.style.boxShadow = '0 8px 24px rgba(25, 24, 59, 0.12)';
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
            // Clear any breathing overlays when hiding results
            try {
                const existingOverlay = document.getElementById('imageOverlay');
                if (existingOverlay) existingOverlay.remove();
            } catch (_) {}
        }
        
        // Inject breathing animation CSS once
        (function injectBreathingStyles() {
            if (document.getElementById('breathingMaskStyles')) return;
            const style = document.createElement('style');
            style.id = 'breathingMaskStyles';
            style.textContent = `
@keyframes breathe{0%,100%{opacity:.35;filter:drop-shadow(0 0 0px rgba(105,108,255,.65))}50%{opacity:.55;filter:drop-shadow(0 0 14px rgba(105,108,255,.65))}}
.image-overlay{position:absolute;inset:0;pointer-events:none}
.pepper-mask{position:absolute;background:rgba(105,108,255,.85);animation:breathe 2s ease-in-out infinite;-webkit-mask-repeat:no-repeat;-webkit-mask-size:100% 100%;mask-repeat:no-repeat;mask-size:100% 100%;transition:opacity .2s ease;pointer-events:auto}
.pepper-mask:hover{opacity:0}
`;
            document.head.appendChild(style);
        })();
        
        // Utilities to manage overlays
        function clearOverlays() {
            const overlay = document.getElementById('imageOverlay');
            if (overlay) overlay.remove();
        }
        
        function renderBreathingOverlays(imgEl, peppers, originalWidth, originalHeight) {
            if (!imgEl || !peppers || peppers.length === 0 || !originalWidth || !originalHeight) {
                clearOverlays();
                return;
            }
            
            clearOverlays();
            const wrapper = imgEl.parentElement || imageContainer;
            if (!wrapper) return;
            // Ensure wrapper can host absolute overlay
            if (getComputedStyle(wrapper).position === 'static') {
                wrapper.style.position = 'relative';
            }
            
            const overlay = document.createElement('div');
            overlay.id = 'imageOverlay';
            overlay.className = 'image-overlay';
            wrapper.appendChild(overlay);
            
            const displayWidth = imgEl.clientWidth || imgEl.width;
            const displayHeight = imgEl.clientHeight || imgEl.height;
            if (!displayWidth || !displayHeight) return;
            
            const scaleX = displayWidth / originalWidth;
            const scaleY = displayHeight / originalHeight;
            
            peppers.forEach(p => {
                if (!p || !p.transparent_png_url || !p.bbox) return;
                const b = p.bbox;
                if (typeof b.x !== 'number' || typeof b.y !== 'number' || typeof b.width !== 'number' || typeof b.height !== 'number') return;
                
                const el = document.createElement('div');
                el.className = 'pepper-mask';
                el.style.left = (b.x * scaleX) + 'px';
                el.style.top = (b.y * scaleY) + 'px';
                el.style.width = (b.width * scaleX) + 'px';
                el.style.height = (b.height * scaleY) + 'px';
                // Use the object cutout as a mask image
                const maskUrl = p.transparent_png_url + '?t=' + Date.now();
                el.style.webkitMaskImage = `url(${maskUrl})`;
                el.style.maskImage = `url(${maskUrl})`;
                // Base tint strength
                el.style.opacity = '0.4';
                overlay.appendChild(el);
            });
        }
        
        function resetUploadPreview() {
            const fileLabel = document.querySelector('.file-label');
            const uploadIcon = fileLabel.querySelector('.upload-icon');
            const uploadText = fileLabel.querySelector('.upload-text');
            const existingPreview = fileLabel.querySelector('img');
            
            // Remove existing preview image
            if (existingPreview) {
                existingPreview.remove();
            }
            
            // Restore original content
            uploadIcon.style.display = 'block';
            uploadText.innerHTML = `
                <span class="upload-main">Choose a file or drag it here</span>
                <small class="upload-sub">Supported formats: JPG, PNG, GIF, WebP</small>
            `;
        }
        
        function displayGeneralObjects(objects) {
            if (!objects || objects.length === 0) {
                generalSection.style.display = 'none';
                return;
            }
            
            // Show warning message instead of listing objects
            generalSection.style.display = 'block';
            generalObjects.innerHTML = `
                <div class="non-pepper-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div class="warning-content">
                        <h4>Non-Pepper Objects Detected</h4>
                        <p>This is not a bell pepper. ${objects.length} other object(s) detected in the image.</p>
                        <small>Only bell peppers are analyzed for quality assessment.</small>
                    </div>
                </div>
            `;
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
        
        // Philippines Bell Pepper Usage Suggestions
        function getPhilippinesPepperSuggestions() {
            return {
                'Green': {
                    emoji: '🟢',
                    name: 'Green Bell Pepper',
                    tagalog: 'Pinaka-karaniwan',
                    taste: 'Slightly bitter, crunchy',
                    bestFor: [
                        'Sinigang na Baboy (garnish near the end of cooking)',
                        'Menudo, Mechado, Afritada',
                        'Stir-fry gulay like chopsuey',
                        'Pinoy pizza & pancit'
                    ],
                    otherUses: [
                        'Most affordable for bulk cooking in carinderias',
                        'Adds aroma and color to viands'
                    ]
                },
                'Red': {
                    emoji: '🔴',
                    name: 'Red Bell Pepper',
                    tagalog: 'Hinog na green pepper',
                    taste: 'Sweeter, strong aroma',
                    bestFor: [
                        'Sweet & sour dishes (Isda/Manok)',
                        'Embutido, Lumpiang Shanghai mix',
                        'Salads & fresh side dishes',
                        'Inihaw with BBQ & kebabs'
                    ],
                    otherUses: [
                        'Garnishing for fiestas and events',
                        'High Vitamin C for healthy snacks'
                    ]
                },
                'Yellow': {
                    emoji: '🟡',
                    name: 'Yellow Bell Pepper',
                    tagalog: '',
                    taste: 'Sweet & fruity',
                    bestFor: [
                        'Pasta dishes, carbonara toppings',
                        'Burger & sandwich palaman',
                        'Vegetable lumpia',
                        'Salad bar sa hotel & restaurants'
                    ],
                    otherUses: [
                        'Gives bright color variety for food presentation'
                    ]
                },
                'Orange': {
                    emoji: '🟠',
                    name: 'Orange Bell Pepper',
                    tagalog: '',
                    taste: 'Sweet and crunchy',
                    bestFor: [
                        "Kids' baon/snacks (hindi maanghang)",
                        'Stuffed bell pepper',
                        'Colorful chopsuey and sautéed dishes'
                    ],
                    otherUses: [
                        'Attractive for party platters and catering'
                    ]
                },
                'Mini': {
                    emoji: '🟣',
                    name: 'Mini Bell Peppers',
                    tagalog: 'Available in supermarkets, some farms in Benguet & Bukidnon',
                    taste: 'Sweet small-size',
                    bestFor: [
                        'Healthy baon',
                        'Appetizers filled with cream cheese or tuna spread',
                        'Sushi and fusion cooking'
                    ],
                    otherUses: [
                        'Decorative vegetable for plating'
                    ]
                }
            };
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
                                ${shelfLife.carrier ? `
                                <div class="carrier-section">
                                    <h5 style="margin: 8px 0 4px 0;"><i class="fas fa-truck"></i> Carrier Shelf Life</h5>
                                    <div class="carrier-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:10px; align-items:stretch;">
                                        ${shelfLife.carrier.truck_refrigerated ? `<div class="storage-option" style="display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid var(--gray); border-radius: var(--border-radius-sm); background: var(--card-bg);"><span><i class="fas fa-truck"></i> Truck (Refrigerated)</span><span class="storage-duration">${shelfLife.carrier.truck_refrigerated.days} days</span></div>` : ''}
                                        ${shelfLife.carrier.truck_non_refrigerated ? `<div class="storage-option" style="display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid var(--gray); border-radius: var(--border-radius-sm); background: var(--card-bg);"><span><i class="fas fa-truck-monster"></i> Truck (Non‑refrig)</span><span class="storage-duration">${shelfLife.carrier.truck_non_refrigerated.days} days</span></div>` : ''}
                                        ${shelfLife.carrier.boat ? `<div class="storage-option" style="display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid var(--gray); border-radius: var(--border-radius-sm); background: var(--card-bg);"><span><i class="fas fa-ship"></i> Boat</span><span class="storage-duration">${shelfLife.carrier.boat.days} days</span></div>` : ''}
                                        ${shelfLife.carrier.air_cargo ? `<div class="storage-option" style="display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid var(--gray); border-radius: var(--border-radius-sm); background: var(--card-bg);"><span><i class="fas fa-plane"></i> Air Cargo</span><span class="storage-duration">${shelfLife.carrier.air_cargo.days} days</span></div>` : ''}
                                    </div>
                                </div>` : ''}
                            </div>
                        </div>
                    `;
                }
                
                // Generate Filipino Cuisine Suggestions Based on Analysis
                function generateAnalysisBasedSuggestions(pepper) {
                    const qa = pepper.quality_analysis || {};
                    const ripeness = pepper.ripeness_prediction || {};
                    const nutrition = pepper.nutrition || {};
                    const variety = pepper.variety || 'Green';
                    const varietyKey = variety.split(' ')[0];
                    const usageRecs = pepper.usage_recommendations || {};
                    
                    const qualityScore = qa.quality_score || 50;
                    const ripenessLevel = qa.ripeness_level || 50;
                    const surfaceQuality = qa.surface_quality || 50;
                    const colorUniformity = qa.color_uniformity || 50;
                    const ripenessStage = ripeness.current_stage || '';
                    const vitaminC = nutrition.per_pepper?.vitamin_c || 0;
                    
                    // Get variety base info
                    const suggestionsData = getPhilippinesPepperSuggestions();
                    const varietyInfo = suggestionsData[varietyKey] || suggestionsData['Green'];
                    
                    let bestFor = [];
                    
                    // Check if suitable for salad (from backend analysis)
                    const suitableForSalad = usageRecs.suitable_for_salad || 
                        (ripenessLevel >= 60 && surfaceQuality >= 70 && 
                         (varietyKey === 'Red' || varietyKey === 'Yellow' || varietyKey === 'Orange'));
                    
                    // Analysis-based suggestions
                    // High quality + high ripeness = fresh/raw uses (salads)
                    if (suitableForSalad) {
                        bestFor.push('🥗 Salads & fresh side dishes');
                        bestFor.push('Garnishing for fiestas and events');
                        if (vitaminC >= 250) {
                            bestFor.push('Healthy snacks (high Vitamin C)');
                        }
                    } else if (qualityScore >= 70 && ripenessLevel >= 70) {
                        if (varietyKey === 'Red' || varietyKey === 'Yellow' || varietyKey === 'Orange') {
                            bestFor.push('Salads & fresh side dishes (when fully ripe)');
                            bestFor.push('Garnishing for fiestas and events');
                        }
                        if (vitaminC >= 250) {
                            bestFor.push('Healthy snacks (high Vitamin C)');
                        }
                    }
                    
                    // Medium to high ripeness = sweet dishes
                    if (ripenessLevel >= 60) {
                        bestFor.push('Sweet & sour dishes (Isda/Manok)');
                        if (varietyKey === 'Red') {
                            bestFor.push('Embutido, Lumpiang Shanghai mix');
                        }
                    }
                    
                    // Low quality or poor surface = cooked dishes (masks imperfections)
                    if (qualityScore < 60 || surfaceQuality < 50) {
                        bestFor.push('Sinigang na Baboy (garnish near the end)');
                        bestFor.push('Menudo, Mechado, Afritada');
                        bestFor.push('Stir-fry gulay like chopsuey');
                    } else {
                        // Good quality = versatile uses
                        if (varietyKey === 'Green') {
                            bestFor.push('Menudo, Mechado, Afritada');
                            bestFor.push('Pinoy pizza & pancit');
                        } else if (varietyKey === 'Red') {
                            bestFor.push('Inihaw with BBQ & kebabs');
                        } else if (varietyKey === 'Yellow' || varietyKey === 'Orange') {
                            bestFor.push('Pasta dishes, carbonara toppings');
                            bestFor.push('Colorful chopsuey and sautéed dishes');
                        }
                    }
                    
                    // Always add common Filipino dishes based on variety if list is empty
                    if (bestFor.length === 0) {
                        bestFor = varietyInfo.bestFor.slice(0, 3);
                    }
                    
                    return {
                        emoji: varietyInfo.emoji,
                        name: varietyInfo.name,
                        tagalog: varietyInfo.tagalog,
                        taste: varietyInfo.taste,
                        bestFor: bestFor.slice(0, 3),
                        suitableForSalad: suitableForSalad
                    };
                }
                
                // Market Analysis - Usage Recommendations Based on Analysis
                let marketAnalysisHTML = '';
                
                // Use the SAME data sources as ripeness prediction, shelf life, and nutrition
                // Get ripeness percentage from ripeness_prediction (same as ripeness analysis display)
                const ripeness = pepper.ripeness_prediction || {};
                const ripenessPercentage = ripeness.ripeness_percentage || 0;
                
                // Get surface quality from quality_analysis (same as other analyses)
                const qa = pepper.quality_analysis || {};
                const surfaceQuality = qa.surface_quality || 0;
                
                // Get variety
                const variety = pepper.variety || 'Green';
                const varietyKey = variety.split(' ')[0];
                
                // Check disease status (same logic as other analyses)
                let hasDisease = false;
                if (pepper.disease_analysis) {
                    const disease = pepper.disease_analysis;
                    if (typeof disease === 'object') {
                        hasDisease = !disease.is_healthy || (disease.disease && disease.disease !== 'Healthy');
                    } else if (typeof disease === 'string') {
                        try {
                            const diseaseParsed = JSON.parse(disease);
                            hasDisease = !diseaseParsed.is_healthy || (diseaseParsed.disease && diseaseParsed.disease !== 'Healthy');
                        } catch (e) {
                            hasDisease = false;
                        }
                    }
                }
                
                // Check for defects in recommendations
                let hasDefect = false;
                let defectMessage = '';
                if (qa.recommendations && qa.recommendations.length > 0) {
                    const defectKeywords = [
                        'defect', 'defects', 'damage', 'damaged', 'inspect', 'inspection',
                        'surface defect', 'surface defects', 'surface damage', 'damage or disease',
                        'poor quality', 'quality issue', 'quality issues', 'blemish', 'blemishes',
                        'bruise', 'bruised', 'crack', 'cracked', 'rot', 'rotting', 'decay', 'decaying'
                    ];
                    
                    for (const rec of qa.recommendations) {
                        const recLower = rec.toLowerCase();
                        for (const keyword of defectKeywords) {
                            if (recLower.includes(keyword)) {
                                hasDefect = true;
                                defectMessage = rec;
                                break;
                            }
                        }
                        if (hasDefect) break;
                    }
                }
                
                // Determine usage badges based on SAME data sources as other analyses
                const badges = [];
                
                // Determine suitability flags (needed for detailed information)
                let isSaladSuitable = false;
                let isCookingSuitable = false;
                let isSauceSuitable = false;
                
                // Only show badges if no disease detected AND no defects detected
                if (!hasDisease && !hasDefect) {
                    // Salad suitability: Use ripeness_percentage from ripeness_prediction (same source)
                    // Criteria: ripeness >= 60%, surface quality >= 70%, healthy, Red/Yellow/Orange variety
                    isSaladSuitable = (
                        ripenessPercentage >= 60 && 
                        surfaceQuality >= 70 && 
                        (varietyKey === 'Red' || varietyKey === 'Yellow' || varietyKey === 'Orange')
                    );
                    
                    // Cooking suitability: Use ripeness_percentage from ripeness_prediction
                    // Suitable for cooking when ripeness is 30-80% (medium ripeness)
                    isCookingSuitable = (
                        ripenessPercentage >= 30 && ripenessPercentage < 80
                    );
                    
                    // Sauce suitability: Use ripeness_percentage from ripeness_prediction
                    // Very ripe (>=80%) or low surface quality (<50%) - best for processing
                    isSauceSuitable = (
                        ripenessPercentage >= 80 || surfaceQuality < 50
                    );
                    
                    // Add salad badge if suitable
                    if (isSaladSuitable) {
                        badges.push('<span class="usage-badge usage-badge-salad" title="Suitable for fresh salads and raw consumption"><span class="usage-emoji">🥗</span> Suitable for salads</span>');
                    }
                    
                    // Add cooking badge if suitable (or as default if no other badges)
                    if (isCookingSuitable || (!isSaladSuitable && !isSauceSuitable)) {
                        badges.push('<span class="usage-badge usage-badge-cooking" title="Best for cooking and prepared dishes"><span class="usage-emoji">🍽</span> Best for cooking</span>');
                    }
                    
                    // Add sauce badge if suitable
                    if (isSauceSuitable) {
                        badges.push('<span class="usage-badge usage-badge-sauce" title="Ideal for sauces, seasoning, and processing"><span class="usage-emoji">🌶</span> For sauces or seasoning</span>');
                    }
                }
                
                const market = pepper.market_analysis;
                const gradeClass = market ? market.grade.toLowerCase().replace(' ', '-') : '';
                
                if (pepper.market_analysis || badges.length > 0) {
                    marketAnalysisHTML = `
                        <div class="market-analysis-compact">
                            <div class="analysis-header">
                                <h4><i class="fas fa-chart-line"></i> Market Analysis</h4>
                            </div>
                            <div class="market-content-compact">
                                ${market ? `
                                <div class="market-grade-compact ${gradeClass}">
                                    <span class="grade-name-compact">${market.grade}</span>
                                    <span class="grade-description-compact">${market.grade_description}</span>
                                </div>
                                ${market.estimated_price_per_kg ? `
                                <div class="market-price-compact">
                                    <i class="fas fa-peso-sign"></i>
                                    <span>₱${market.estimated_price_per_kg}/kg</span>
                                </div>` : ''}` : ''}
                                
                                ${badges.length > 0 ? `
                                <div class="market-usage-section">
                                    <div class="usage-header">
                                        <i class="fas fa-utensils"></i>
                                        <span>Usage Recommendations</span>
                                    </div>
                                    <div class="usage-badges-container">
                                        ${badges.join('')}
                                    </div>
                                    <div class="usage-details">
                                        ${isSaladSuitable ? `
                                        <div class="usage-detail-item">
                                            <div class="usage-detail-header">
                                                <span class="usage-emoji">🥗</span>
                                                <strong>Suitable for Salads</strong>
                                            </div>
                                            <div class="usage-detail-content">
                                                <p>This ${variety} bell pepper is ideal for fresh consumption in salads due to:</p>
                                                <ul>
                                                    <li>Ripeness level: ${ripenessPercentage.toFixed(1)}% (optimal for raw consumption)</li>
                                                    <li>Surface quality: ${surfaceQuality.toFixed(1)}% (excellent condition)</li>
                                                    <li>Variety: ${varietyKey} peppers are naturally sweeter and perfect for salads</li>
                                                    <li>Health status: Healthy and safe for raw consumption</li>
                                                </ul>
                                                <p class="usage-suggestion"><strong>Best uses:</strong> Fresh salads, garnishing, healthy snacks, side dishes, and raw consumption in Filipino cuisine like fresh lumpia or kinilaw preparations.</p>
                                            </div>
                                        </div>` : ''}
                                        ${isCookingSuitable ? `
                                        <div class="usage-detail-item">
                                            <div class="usage-detail-header">
                                                <span class="usage-emoji">🍽</span>
                                                <strong>Best for Cooking</strong>
                                            </div>
                                            <div class="usage-detail-content">
                                                <p>This ${variety} bell pepper is excellent for cooking and prepared dishes:</p>
                                                <ul>
                                                    <li>Ripeness level: ${ripenessPercentage.toFixed(1)}% (ideal for cooking - retains texture and flavor)</li>
                                                    <li>Surface quality: ${surfaceQuality.toFixed(1)}% (good condition for processing)</li>
                                                    <li>Variety: ${varietyKey} peppers add great flavor and color to cooked dishes</li>
                                                </ul>
                                                <p class="usage-suggestion"><strong>Best uses:</strong> Sinigang, Menudo, Mechado, Afritada, stir-fry dishes (chopsuey), Pinoy pizza, pancit, and other Filipino cooked dishes. The medium ripeness ensures it maintains its shape and texture during cooking.</p>
                                            </div>
                                        </div>` : ''}
                                        ${isSauceSuitable ? `
                                        <div class="usage-detail-item">
                                            <div class="usage-detail-header">
                                                <span class="usage-emoji">🌶</span>
                                                <strong>For Sauces or Seasoning</strong>
                                            </div>
                                            <div class="usage-detail-content">
                                                <p>This ${variety} bell pepper is recommended for sauces, seasoning, and food processing:</p>
                                                <ul>
                                                    <li>Ripeness level: ${ripenessPercentage.toFixed(1)}% (${ripenessPercentage >= 80 ? 'very ripe - maximum flavor' : 'optimal for processing'})</li>
                                                    <li>Surface quality: ${surfaceQuality.toFixed(1)}% (${surfaceQuality < 50 ? 'lower quality - better suited for processing' : 'good for processing'})</li>
                                                    <li>Variety: ${varietyKey} peppers provide rich flavor when processed</li>
                                                </ul>
                                                <p class="usage-suggestion"><strong>Best uses:</strong> Making sauces, pickles, relishes, seasoning blends, food processing, and value-added products. The high ripeness or processing-friendly quality makes it perfect for these applications.</p>
                                            </div>
                                        </div>` : ''}
                                        <div class="usage-analysis-summary">
                                            <div class="usage-summary-item">
                                                <span class="usage-summary-label">Ripeness:</span>
                                                <span class="usage-summary-value">${ripenessPercentage.toFixed(1)}%</span>
                                            </div>
                                            <div class="usage-summary-item">
                                                <span class="usage-summary-label">Surface Quality:</span>
                                                <span class="usage-summary-value">${surfaceQuality.toFixed(1)}%</span>
                                            </div>
                                            <div class="usage-summary-item">
                                                <span class="usage-summary-label">Variety:</span>
                                                <span class="usage-summary-value">${variety}</span>
                                            </div>
                                            <div class="usage-summary-item">
                                                <span class="usage-summary-label">Health Status:</span>
                                                <span class="usage-summary-value">${hasDisease ? '<span style="color: #ef4444;">Disease Detected</span>' : hasDefect ? '<span style="color: #f59e0b;">Defect Detected</span>' : '<span style="color: #10b981;">Healthy</span>'}</span>
                                            </div>
                                            ${hasDefect ? `
                                            <div class="usage-summary-item" style="grid-column: 1 / -1;">
                                                <span class="usage-summary-label">Defect Information:</span>
                                                <span class="usage-summary-value" style="color: #f59e0b; font-size: 0.85rem;">${defectMessage || 'Surface defects or damage detected'}</span>
                                            </div>` : ''}
                                        </div>
                                    </div>
                                    ${hasDisease || hasDefect ? `
                                    <div class="usage-warning">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        <span>${hasDefect ? 'Defect Detected' : 'Usage recommendations not available due to detected disease'}</span>
                                    </div>` : ''}
                                </div>` : (hasDisease || hasDefect ? `
                                <div class="market-usage-section">
                                    <div class="usage-warning">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        <span>${hasDefect ? `Defect Detected: ${defectMessage || 'Surface defects or damage detected. Please inspect the pepper before consumption.'}` : 'Usage recommendations not available - disease detected. Please treat the pepper before consumption.'}</span>
                                    </div>
                                </div>` : '')}
                            </div>
                        </div>
                    `;
                }
                
                // Combine all advanced analyses - wrap in collapsible container
                let advancedAnalysisToggleHTML = '';
                if (ripenessAnalysisHTML || nutritionAnalysisHTML || shelfLifeHTML || marketAnalysisHTML) {
                    const analysisId = `advanced-analysis-${pepper.pepper_id || index}`;
                    advancedAnalysisToggleHTML = `
                        <div class="advanced-analysis-toggle-section">
                            <button class="btn-toggle-analysis" onclick="toggleAdvancedAnalysis('${analysisId}')" aria-expanded="false">
                                <i class="fas fa-chevron-down"></i>
                                <span>View Full Analysis</span>
                            </button>
                            <div id="${analysisId}" class="advanced-analysis-collapsible" style="display: none;">
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
                
                // Usage badges are now displayed in Market Analysis section (removed from here)
                
                html += `
                <div class="detection-item pepper-item" style="animation-delay: ${index * 0.1}s">
                    <div class="pepper-header">
                        ${pepper.transparent_png_url ? `<img src="${pepper.transparent_png_url}?t=${Date.now()}" alt="Bell Pepper ${pepper.pepper_id}" class="pepper-crop-image" style="background: transparent; object-fit: contain;">` : (pepper.crop_url ? `<img src="${pepper.crop_url}?t=${Date.now()}" alt="Bell Pepper ${pepper.pepper_id}" class="pepper-crop-image">` : '')}
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
                    ${advancedAnalysisToggleHTML}
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
                
                // Show preview of selected image in the upload area
                const file = fileInput.files[0];
                const reader = new FileReader();
                reader.onload = function(e) {
                    const fileLabel = document.querySelector('.file-label');
                    const uploadIcon = fileLabel.querySelector('.upload-icon');
                    const uploadText = fileLabel.querySelector('.upload-text');
                    
                    // Create preview image
                    const previewImg = document.createElement('img');
                    previewImg.src = e.target.result;
                    previewImg.style.cssText = 'max-width: 100%; max-height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;';
                    
                    // Hide original content and show preview
                    uploadIcon.style.display = 'none';
                    uploadText.innerHTML = `
                        <span class="upload-main">${file.name}</span>
                        <small class="upload-sub">Click to change image</small>
                    `;
                    
                    // Insert preview image
                    fileLabel.insertBefore(previewImg, uploadText);
                };
                reader.readAsDataURL(file);
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
                
                // Reset upload preview when analysis starts
                resetUploadPreview();
                
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

        // Progress bar functions
        function showProgressBar() {
            // Create progress bar container if it doesn't exist
            let progressContainer = document.getElementById('progressContainer');
            if (!progressContainer) {
                progressContainer = document.createElement('div');
                progressContainer.id = 'progressContainer';
                progressContainer.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: var(--card-bg);
                    backdrop-filter: blur(20px);
                    padding: 2rem;
                    border-radius: var(--border-radius);
                    box-shadow: var(--box-shadow-lg);
                    z-index: 9999;
                    min-width: 400px;
                    max-width: 90vw;
                `;
                
                progressContainer.innerHTML = `
                    <div style="text-align: center; margin-bottom: 1.5rem;">
                        <div style="width: 60px; height: 60px; background: var(--primary-light); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; animation: pulse 2s infinite;">
                            <i class="fas fa-brain" style="font-size: 1.75rem; color: var(--primary);"></i>
                        </div>
                        <h3 style="margin: 0 0 0.5rem 0; color: var(--dark); font-size: 1.25rem;">Analyzing Bell Peppers</h3>
                        <p id="progressText" style="color: var(--secondary); margin: 0; font-size: 0.9rem;">Initializing...</p>
                    </div>
                    
                    <div style="background: var(--gray-light); border-radius: 50px; height: 12px; overflow: hidden; margin-bottom: 1rem; position: relative;">
                        <div id="progressBar" style="height: 100%; background: linear-gradient(90deg, var(--primary), var(--info)); border-radius: 50px; width: 0%; transition: width 0.3s ease; position: relative;">
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent); animation: shimmer 1.5s infinite;"></div>
                        </div>
                    </div>
                    
                    <div id="progressSteps" style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem;">
                        <div id="step1" style="display: flex; align-items: center; gap: 0.5rem; color: var(--secondary);">
                            <i class="fas fa-circle-notch fa-spin"></i>
                            <span>Uploading image...</span>
                        </div>
                        <div id="step2" style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray); opacity: 0.5;">
                            <i class="fas fa-circle"></i>
                            <span>Detecting objects...</span>
                        </div>
                        <div id="step3" style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray); opacity: 0.5;">
                            <i class="fas fa-circle"></i>
                            <span>Analyzing quality...</span>
                        </div>
                        <div id="step4" style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray); opacity: 0.5;">
                            <i class="fas fa-circle"></i>
                            <span>Saving results...</span>
                        </div>
                    </div>
                `;
                
                // Add overlay
                const overlay = document.createElement('div');
                overlay.id = 'progressOverlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 9998;
                    backdrop-filter: blur(4px);
                `;
                
                document.body.appendChild(overlay);
                document.body.appendChild(progressContainer);
            }
        }
        
        function updateProgress(step, percentage, text) {
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            
            if (progressBar) progressBar.style.width = percentage + '%';
            if (progressText) progressText.textContent = text;
            
            // Update step indicators
            const steps = ['step1', 'step2', 'step3', 'step4'];
            steps.forEach((stepId, index) => {
                const stepEl = document.getElementById(stepId);
                if (stepEl) {
                    const icon = stepEl.querySelector('i');
                    if (index < step) {
                        // Completed step
                        stepEl.style.color = 'var(--success)';
                        stepEl.style.opacity = '1';
                        icon.className = 'fas fa-check-circle';
                    } else if (index === step) {
                        // Current step
                        stepEl.style.color = 'var(--primary)';
                        stepEl.style.opacity = '1';
                        icon.className = 'fas fa-circle-notch fa-spin';
                    } else {
                        // Pending step
                        stepEl.style.color = 'var(--gray)';
                        stepEl.style.opacity = '0.5';
                        icon.className = 'fas fa-circle';
                    }
                }
            });
        }
        
        function hideProgressBar() {
            const progressContainer = document.getElementById('progressContainer');
            const progressOverlay = document.getElementById('progressOverlay');
            
            if (progressContainer) {
                progressContainer.style.transition = 'opacity 0.3s';
                progressContainer.style.opacity = '0';
                setTimeout(() => progressContainer.remove(), 300);
            }
            if (progressOverlay) {
                progressOverlay.style.transition = 'opacity 0.3s';
                progressOverlay.style.opacity = '0';
                setTimeout(() => progressOverlay.remove(), 300);
            }
        }

        async function sendForm(fd) {
            processingStartTime = Date.now();
            updateStatus('Processing image...', 'info', true);
            hideResults();
            
            // Check if offline
            if (!isOnline) {
                await queueUploadForLater(fd);
                return;
            }
            
            // Show progress bar
            showProgressBar();
            updateProgress(0, 10, 'Uploading image...');
            
            try {
                // Simulate upload progress
                setTimeout(() => updateProgress(1, 30, 'Detecting objects with YOLOv8...'), 300);
                
                const resp = await fetch('/upload', { method: 'POST', body: fd });
                
                // Check if upload failed due to offline
                if (!resp.ok) {
                    const errorData = await resp.json().catch(() => ({}));
                    if (errorData.offline || errorData.queued) {
                        hideProgressBar();
                        await queueUploadForLater(fd);
                        return;
                    }
                }
                
                // Update progress during fetch
                updateProgress(2, 60, 'Analyzing quality with ANFIS...');
                
                const data = await resp.json();
                
                updateProgress(3, 90, 'Saving to database...');
                
                if (!resp.ok) {
                    hideProgressBar();
                    throw new Error(data.error || `Server error: ${resp.status}`);
                }
                
                updateProgress(4, 100, 'Complete!');
                
                // Save to offline cache
                if (offlineStorageReady) {
                    try {
                        await window.offlineStorage.saveAnalysis({
                            ...data,
                            processing_time: Date.now() - processingStartTime
                        });
                    } catch (err) {
                        console.warn('Failed to cache analysis:', err);
                    }
                }
                
                // Calculate processing time
                const processingTimeMs = Date.now() - processingStartTime;
                
                // Show clean base image (no labels) for overlay rendering with safe fallbacks
                const baseImageUrl = data.original_image_url || data.result_url || data.image_url;
                if (!baseImageUrl) {
                    console.warn('No base image URL found on response. Expected original_image_url/result_url/image_url.', data);
                }
                previewImg.src = (baseImageUrl || '') + (baseImageUrl ? ('?t=' + Date.now()) : '');
                
                // Determine image orientation and apply appropriate container class
                const peppersLocal = data.bell_peppers || [];
                previewImg.onload = function() {
                    const imageContainer = document.getElementById('imageContainer');
                    imageContainer.classList.remove('landscape', 'portrait');
                    
                    if (this.naturalWidth > this.naturalHeight) {
                        imageContainer.classList.add('landscape');
                    } else {
                        imageContainer.classList.add('portrait');
                    }
                    
                    // Render breathing overlays aligned to displayed size
                    renderBreathingOverlays(previewImg, peppersLocal, this.naturalWidth, this.naturalHeight);
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
                
                // Auto-scroll to Bell Pepper Detection section if peppers were found
                if (data.bell_peppers && data.bell_peppers.length > 0) {
                    setTimeout(() => {
                        const pepperSection = document.getElementById('pepperSection');
                        if (pepperSection) {
                            pepperSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 100);
                }
                
                // Hide progress bar after short delay
                setTimeout(() => hideProgressBar(), 500);
            } catch (err) {
                hideProgressBar();
                handleError(err, 'image processing');
            }
        }

        // Toggle Advanced Analysis Function
        window.toggleAdvancedAnalysis = function(analysisId) {
            const collapsible = document.getElementById(analysisId);
            if (!collapsible) return;
            
            // Find the button - it's the previous sibling in the parent container
            const toggleSection = collapsible.parentElement;
            const button = toggleSection?.querySelector('.btn-toggle-analysis');
            
            if (!button) return;
            
            const isExpanded = collapsible.style.display !== 'none';
            const icon = button.querySelector('i');
            const span = button.querySelector('span');
            
            if (isExpanded) {
                // Collapse
                collapsible.style.display = 'none';
                if (icon) icon.className = 'fas fa-chevron-down';
                if (span) span.textContent = 'View Full Analysis';
                button.setAttribute('aria-expanded', 'false');
            } else {
                // Expand
                collapsible.style.display = 'block';
                if (icon) icon.className = 'fas fa-chevron-up';
                if (span) span.textContent = 'Hide Full Analysis';
                button.setAttribute('aria-expanded', 'true');
                
                // Smooth scroll to the expanded section
                setTimeout(() => {
                    collapsible.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        };

        // Full Analysis Modal Functions (make globally accessible)
        window.openFullAnalysisModal = function() {
            const modal = document.getElementById('fullAnalysisModal');
            const content = document.getElementById('fullAnalysisContent');
            const suggestionsData = getPhilippinesPepperSuggestions();
            
            if (!modal || !content) return;
            
            // Build HTML for all varieties
            let html = '';
            const varieties = ['Green', 'Red', 'Yellow', 'Orange', 'Mini'];
            
            varieties.forEach((varietyKey, index) => {
                const suggestion = suggestionsData[varietyKey];
                if (!suggestion) return;
                
                html += `
                    <div class="variety-card" style="animation-delay: ${index * 0.1}s">
                        <div class="variety-header">
                            <span class="variety-number">${index + 1}️⃣</span>
                            <div class="variety-title-group">
                                <h3>
                                    <span class="variety-emoji-large">${suggestion.emoji}</span>
                                    ${suggestion.name}
                                </h3>
                                ${suggestion.tagalog ? `<p class="variety-tagalog">${suggestion.tagalog}</p>` : ''}
                            </div>
                        </div>
                        <div class="variety-content">
                            <div class="variety-taste">
                                <strong>Taste:</strong> ${suggestion.taste}
                            </div>
                            <div class="variety-best-for">
                                <strong>Best For:</strong>
                                <ul>
                                    ${suggestion.bestFor.map(use => `<li>${use}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="variety-other-uses">
                                <strong>Other Uses:</strong>
                                <ul>
                                    ${suggestion.otherUses.map(use => `<li>${use}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            content.innerHTML = html;
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        };

        window.closeFullAnalysisModal = function() {
            const modal = document.getElementById('fullAnalysisModal');
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scrolling
            }
        };

        // Close modal when clicking outside
        document.addEventListener('DOMContentLoaded', () => {
            const modal = document.getElementById('fullAnalysisModal');
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        closeFullAnalysisModal();
                    }
                });
            }
            
            // Close modal on Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const modal = document.getElementById('fullAnalysisModal');
                    if (modal && modal.style.display === 'flex') {
                        closeFullAnalysisModal();
                    }
                }
            });
        });

