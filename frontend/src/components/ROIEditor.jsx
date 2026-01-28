import React, { useRef, useState, useEffect } from 'react';

const ROIEditor = ({ masterImageStr, initialRois = [], onSave, onClose }) => {
    const canvasRef = useRef(null);
    const [rois, setRois] = useState(initialRois);
    const [isDrawing, setIsDrawing] = useState(false);
    const [startPos, setStartPos] = useState({ x: 0, y: 0 });
    const [currentRect, setCurrentRect] = useState(null);
    const [mode, setMode] = useState('exclude'); // 'include' or 'exclude'
    const [zoom, setZoom] = useState(0.7);

    useEffect(() => {
        draw();
    }, [masterImageStr, rois, currentRect]);

    const getMousePos = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) / zoom,
            y: (e.clientY - rect.top) / zoom
        };
    };

    const handleMouseDown = (e) => {
        setIsDrawing(true);
        setStartPos(getMousePos(e));
    };

    const handleMouseMove = (e) => {
        if (!isDrawing) return;
        const pos = getMousePos(e);
        setCurrentRect({
            x: Math.min(startPos.x, pos.x),
            y: Math.min(startPos.y, pos.y),
            w: Math.abs(pos.x - startPos.x),
            h: Math.abs(pos.y - startPos.y),
            type: mode
        });
    };

    const handleMouseUp = () => {
        if (isDrawing && currentRect) {
            if (currentRect.w > 5 && currentRect.h > 5) {
                setRois([...rois, currentRect]);
            }
        }
        setIsDrawing(false);
        setCurrentRect(null);
    };

    const draw = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const img = new Image();
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            // Draw existing ROIs
            rois.forEach(r => drawRect(ctx, r));

            // Draw current dragging rect
            if (currentRect) drawRect(ctx, currentRect);
        };
        if (masterImageStr) {
            img.src = masterImageStr;
        }
    };

    const drawRect = (ctx, rect) => {
        ctx.strokeStyle = rect.type === 'include' ? '#00C851' : '#ff4444';
        ctx.lineWidth = 3;
        ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);

        ctx.fillStyle = rect.type === 'include' ? 'rgba(0, 200, 81, 0.2)' : 'rgba(255, 68, 68, 0.2)';
        ctx.fillRect(rect.x, rect.y, rect.w, rect.h);
    };

    const deleteLast = () => {
        setRois(rois.slice(0, -1));
    };

    return (
        <div className="roi-modal">
            <div className="roi-toolbar">
                <h3>Editor de Zonas</h3>
                <div className="tools">
                    <button
                        className={mode === 'include' ? 'btn-tool active' : 'btn-tool'}
                        onClick={() => setMode('include')}
                        style={{ borderColor: '#00C851', color: mode === 'include' ? '#fff' : '#00C851' }}
                    >
                        Zona Inspeccion
                    </button>
                    <button
                        className={mode === 'exclude' ? 'btn-tool active' : 'btn-tool'}
                        onClick={() => setMode('exclude')}
                        style={{ borderColor: '#ff4444', color: mode === 'exclude' ? '#fff' : '#ff4444' }}
                    >
                        Zona Exclusion
                    </button>
                    <button className="btn-tool" onClick={deleteLast}>Deshacer</button>
                </div>
                <div className="roi-zoom">
                    <button className="btn-tool" onClick={() => setZoom(Math.max(0.4, zoom - 0.1))}>-</button>
                    <span className="label">Zoom {Math.round(zoom * 100)}%</span>
                    <button className="btn-tool" onClick={() => setZoom(Math.min(2, zoom + 0.1))}>+</button>
                </div>
                <div className="actions">
                    <button className="btn-cancel" onClick={onClose}>Cancelar</button>
                    <button className="btn-save" onClick={() => onSave(rois)}>Guardar Definicion</button>
                </div>
            </div>
            <div className="roi-canvas-container">
                <canvas
                    ref={canvasRef}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    className="roi-canvas"
                    style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
                />
            </div>
        </div>
    );
};

export default ROIEditor;
