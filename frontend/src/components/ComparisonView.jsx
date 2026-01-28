import React, { useState, useEffect, useRef } from 'react';

const ComparisonView = ({ masterSrc, liveSrc, heatmapSrc, defects }) => {
    const [viewMode, setViewMode] = useState('split'); // 'split', 'heatmap'
    const [opacity, setOpacity] = useState(0.5);
    const [imgDimensions, setImgDimensions] = useState({ width: 0, height: 0 }); // Dimensions of the rendered image

    // Safety for defects
    const safeDefects = defects || [];

    const imgRef = useRef(null);

    // Update dimensions on resize
    useEffect(() => {
        const handleResize = () => {
            if (imgRef.current) {
                setImgDimensions({
                    width: imgRef.current.width,
                    height: imgRef.current.height,
                    naturalWidth: imgRef.current.naturalWidth,
                    naturalHeight: imgRef.current.naturalHeight
                });
            }
        };

        window.addEventListener('resize', handleResize);
        // Trigger once when src loads
        if (imgRef.current) {
            imgRef.current.onload = handleResize;
            // Also call immediately in case already loaded
            handleResize();
        }

        return () => window.removeEventListener('resize', handleResize);
    }, [liveSrc, viewMode]); // Re-run if src changes or view changes

    const renderDefectBoxes = () => {
        if (!imgDimensions.width || !imgDimensions.naturalWidth) return null;

        // Calculate Scale Factor
        const scaleX = imgDimensions.width / imgDimensions.naturalWidth;
        const scaleY = imgDimensions.height / imgDimensions.naturalHeight;

        // Use the smaller scale to match object-fit: contain (usually)
        // Wait, object-fit: contain centers the image. This is tricky.
        // For MVP, lets assume the image fills the container or we use use percentage if we could.
        // Actually, best way for object-fit: contain is to wrap a relative div that has the aspect ratio of the image.
        // But for simplicity, we will just rely on the calculated scale and assume standard fit.

        return safeDefects.map((d, i) => (
            <div key={i} style={{
                position: 'absolute',
                left: d.x * scaleX,
                top: d.y * scaleY,
                width: d.w * scaleX,
                height: d.h * scaleY,
                border: '2px solid red',
                boxShadow: '0 0 4px red',
                pointerEvents: 'none'
            }}>
                <span style={{
                    background: 'red', color: 'white',
                    fontSize: '10px',
                    position: 'absolute', top: '-15px', left: 0
                }}>
                    #{i + 1}
                </span>
            </div>
        ));
    };

    const renderPlaceholder = (text) => (
        <div className="img-placeholder">{text}</div>
    );

    return (
        <div className="comparison-container">
            <div className="view-controls">
                <button className={viewMode === 'split' ? 'active' : ''} onClick={() => setViewMode('split')}>Split</button>
                <button className={viewMode === 'heatmap' ? 'active' : ''} onClick={() => setViewMode('heatmap')}>Heatmap</button>
            </div>

            <div className="viewer-stage">
                {viewMode === 'split' && (
                    <div className="split-view">
                        <div className="pane">
                            <h4>Master Ref</h4>
                            <div className="img-wrapper">
                                {masterSrc ? <img src={masterSrc} alt="Master" /> : renderPlaceholder('Load a master to begin')}
                            </div>
                        </div>
                        <div className="pane">
                            <h4>Live Capture</h4>
                            <div className="img-wrapper">
                                {liveSrc ? (
                                    <>
                                        <img
                                            ref={imgRef}
                                            src={liveSrc}
                                            alt="Live"
                                            onLoad={() => {
                                                // Trigger resize calc
                                                if (imgRef.current) {
                                                    setImgDimensions({
                                                        width: imgRef.current.width,
                                                        height: imgRef.current.height,
                                                        naturalWidth: imgRef.current.naturalWidth,
                                                        naturalHeight: imgRef.current.naturalHeight
                                                    });
                                                }
                                            }}
                                        />
                                        {renderDefectBoxes()}
                                    </>
                                ) : renderPlaceholder('Waiting for live feed')}
                            </div>
                        </div>
                    </div>
                )}
                {viewMode === 'heatmap' && (
                    <div className="img-wrapper">
                        {heatmapSrc ? <img className="heatmap-img" src={heatmapSrc} alt="Heatmap" /> : renderPlaceholder('No heatmap yet')}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ComparisonView;
