import React, { useState, useEffect } from 'react';

const RecipeManager = ({ apiUrl = 'http://127.0.0.1:8001', onSelectRecipe, onClose }) => {
    const [recipes, setRecipes] = useState([]);
    const [selectedName, setSelectedName] = useState(null);
    const [recipeData, setRecipeData] = useState(null);
    const [view, setView] = useState('list'); // list, edit

    useEffect(() => {
        loadList();
    }, []);

    const loadList = () => {
        fetch(`${apiUrl}/recipes`)
            .then(res => res.json())
            .then(data => setRecipes(data))
            .catch(err => console.error(err));
    };

    const handleLoad = async (name) => {
        const res = await fetch(`${apiUrl}/load-recipe/${name}`);
        const data = await res.json();
        setRecipeData(data);
        setSelectedName(name);
        setView('edit');
    };

    const handleCreate = () => {
        setRecipeData({
            name: 'New Recipe',
            web_width_mm: 330,
            lane_count: 1,
            rois: [],
            color_targets: [],
            defect_thresholds: { min_area: 50, sensitivity: 30 }
        });
        setSelectedName(null);
        setView('edit');
    };

    const handleClone = async () => {
        if (!selectedName) return;
        const newName = prompt('Enter new name for clone:', selectedName + '_copy');
        if (newName) {
            try {
                await fetch(`${apiUrl}/recipes/${selectedName}/clone?new_name=${newName}`, { method: 'POST' });
                alert('Cloned!');
                loadList();
            } catch (err) {
                console.error(err);
            }
        }
    };

    const handleSave = async () => {
        await fetch(`${apiUrl}/save-recipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(recipeData)
        });
        alert('Saved');
        loadList();
        if (onSelectRecipe) onSelectRecipe(recipeData.name);
        setView('list');
    };

    const renderList = () => (
        <div>
            <div className="row-between">
                <h3>Recipe Library</h3>
                <button onClick={handleCreate}>+ New</button>
            </div>
            <ul className="recipe-list">
                {recipes.map(r => (
                    <li key={r} onClick={() => handleLoad(r)}>
                        {r}
                    </li>
                ))}
            </ul>
            {selectedName && <button onClick={handleClone} className="btn-secondary">Clone Selected</button>}
        </div>
    );

    const renderEdit = () => (
        <div>
            <div className="row-between">
                <h3>Editing: {recipeData.name}</h3>
                <button onClick={() => setView('list')}>Back</button>
            </div>

            <div className="form-group">
                <label>Name:</label>
                <input value={recipeData.name} onChange={e => setRecipeData({ ...recipeData, name: e.target.value })} />
            </div>

            <div className="grid-two">
                <div className="form-group">
                    <label>Width (mm):</label>
                    <input type="number" value={recipeData.web_width_mm} onChange={e => setRecipeData({ ...recipeData, web_width_mm: parseFloat(e.target.value) })} />
                </div>
                <div className="form-group">
                    <label>Lanes:</label>
                    <input type="number" value={recipeData.lane_count} onChange={e => setRecipeData({ ...recipeData, lane_count: parseInt(e.target.value) })} />
                </div>
            </div>

            <div className="form-group">
                <label>Defect Sensitivity:</label>
                <input type="number" value={recipeData.defect_thresholds?.sensitivity || 30}
                    onChange={e => setRecipeData({
                        ...recipeData,
                        defect_thresholds: { ...recipeData.defect_thresholds, sensitivity: parseFloat(e.target.value) }
                    })}
                />
            </div>

            <div className="row gap">
                <button className="btn-primary" onClick={handleSave}>Save</button>
                {onSelectRecipe && <button onClick={() => { onSelectRecipe(recipeData.name); onClose(); }} className="btn-start">Load and Use</button>}
            </div>
        </div>
    );

    return (
        <div className="card recipe-manager">
            {view === 'list' ? renderList() : renderEdit()}
        </div>
    );
};

export default RecipeManager;
