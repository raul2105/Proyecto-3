import React, { useState, useEffect } from 'react';

const ColorSettings = ({ currentTarget, onSave }) => {
    const [form, setForm] = useState({
        name: '',
        l_target: 50,
        a_target: 0,
        b_target: 0,
        tolerance_warning: 2.0,
        tolerance_critical: 5.0
    });

    useEffect(() => {
        if (currentTarget && currentTarget.name) {
            setForm(currentTarget);
        }
    }, [currentTarget]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({
            ...prev,
            [name]: name === 'name' ? value : parseFloat(value)
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(form);
    };

    return (
        <div className="color-settings card">
            <h3>Target Settings</h3>
            <form onSubmit={handleSubmit} className="stack">
                <div className="form-group">
                    <label>Target Name:</label>
                    <input name="name" value={form.name} onChange={handleChange} required />
                </div>
                <div className="grid-two">
                    <div className="form-group">
                        <label>L*:</label>
                        <input type="number" step="0.01" name="l_target" value={form.l_target} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>a*:</label>
                        <input type="number" step="0.01" name="a_target" value={form.a_target} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>b*:</label>
                        <input type="number" step="0.01" name="b_target" value={form.b_target} onChange={handleChange} />
                    </div>
                </div>
                <div className="grid-two">
                    <div className="form-group">
                        <label>Warn Thresh:</label>
                        <input type="number" step="0.1" name="tolerance_warning" value={form.tolerance_warning} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Crit Thresh:</label>
                        <input type="number" step="0.1" name="tolerance_critical" value={form.tolerance_critical} onChange={handleChange} />
                    </div>
                </div>
                <button type="submit" className="btn-primary">
                    Update Target
                </button>
            </form>
        </div>
    );
};

export default ColorSettings;
