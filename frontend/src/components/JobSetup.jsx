import React, { useState, useEffect } from 'react';

const JobSetup = ({ apiUrl = 'http://127.0.0.1:8001', onJobUpdate }) => {
    const [client, setClient] = useState('');
    const [jobNum, setJobNum] = useState('');
    const [rollNum, setRollNum] = useState('');
    const [recipeName, setRecipeName] = useState('');
    const [recipes, setRecipes] = useState([]);

    useEffect(() => {
        loadRecipesList();
    }, [apiUrl]);

    const loadRecipesList = () => {
        fetch(`${apiUrl}/recipes`)
            .then(res => res.json())
            .then(data => setRecipes(data))
            .catch(err => console.error(err));
    };

    const handleSave = async () => {
        if (!recipeName) return alert("Please enter a recipe name");

        const payload = {
            name: recipeName,
            client,
            job_number: jobNum,
            exposure: -6.0 // Ideally mock this or pull from parent state
        };

        const res = await fetch(`${apiUrl}/save-recipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("Recipe saved!");
            loadRecipesList();
        }
    };

    const handleLoad = async (name) => {
        const res = await fetch(`${apiUrl}/load-recipe/${name}`);
        const data = await res.json();

        setClient(data.client || '');
        setJobNum(data.job_number || '');
        setRecipeName(data.name);
        alert(`Loaded recipe: ${name}`);
    };

    return (
        <div className="card job-panel">
            <h3>4. Job Setup</h3>

            <div className="input-row">
                <input placeholder="Client" value={client} onChange={e => setClient(e.target.value)} />
                <input placeholder="Job #" value={jobNum} onChange={e => setJobNum(e.target.value)} />
            </div>

            <div className="input-row">
                <input placeholder="Roll #" value={rollNum} onChange={e => setRollNum(e.target.value)} />
            </div>

            <div className="recipe-row">
                <input
                    placeholder="Recipe Name"
                    value={recipeName}
                    onChange={e => setRecipeName(e.target.value)}
                />
                <button className="btn-save" onClick={handleSave}>Save</button>
            </div>

            <div className="recipe-list">
                <label>Load Recipe:</label>
                <select onChange={(e) => handleLoad(e.target.value)}>
                    <option value="">Select...</option>
                    {recipes.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
            </div>
        </div>
    );
};

export default JobSetup;
