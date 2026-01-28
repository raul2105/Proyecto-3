import React, { useRef, useEffect } from 'react';

const InspectionView = ({ imageSrc, defects }) => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !imageSrc) return;

        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
            // Resize canvas to match image or container?
            // For simplicity, match image dimensions but CSS scales it
            canvas.width = img.width;
            canvas.height = img.height;

            // Draw Image
            ctx.drawImage(img, 0, 0);

            // Draw Defects
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 5;
            ctx.font = '24px Arial';
            ctx.fillStyle = 'red';

            defects.forEach((d, i) => {
                ctx.strokeRect(d.x, d.y, d.w, d.h);
                ctx.fillText(`Defect #${i + 1}`, d.x, d.y - 10);
            });
        };

        if (imageSrc) {
            img.src = imageSrc;
        }
    }, [imageSrc, defects]);

    return (
        <div ref={containerRef} style={{ width: '100%', border: '1px solid #ccc', background: '#000' }}>
            {imageSrc ? (
                <canvas ref={canvasRef} style={{ maxWidth: '100%', height: 'auto' }} />
            ) : (
                <div style={{ padding: '20px', color: '#666', textAlign: 'center' }}>
                    Waiting for video stream...
                </div>
            )}
        </div>
    );
};

export default InspectionView;
