import { useState } from "react";
import "./Settings.css";

function Settings() {
    const [notifications, setNotifications] = useState(true);
    const [safetyAlerts, setSafetyAlerts] = useState(true);

    const name = localStorage.getItem("name") || "Doctor";
    const role = localStorage.getItem("mmss_role") || "doctor";

    return (
        <div className="doctor-settings">

            <section className="doctor-settings__hero">
                <p className="doctor-settings__kicker">
                    ACCOUNT & PREFERENCES
                </p>

                <h1>Settings</h1>

                <p>
                    Manage your doctor profile and workspace preferences.
                </p>
            </section>


            <section className="doctor-settings__panel">

                <div className="doctor-settings__section-header">
                    <p className="doctor-settings__label">
                        PROFILE
                    </p>

                    <h2>Professional Information</h2>
                </div>

                <div className="doctor-settings__profile">

                    <div className="doctor-settings__avatar">
                        Dr
                    </div>

                    <div className="doctor-settings__profile-info">
                        <h3>{name}</h3>
                        <p>Medical Professional</p>
                    </div>

                    <span className="doctor-settings__role">
                        {role}
                    </span>

                </div>

            </section>


            <section className="doctor-settings__panel">

                <div className="doctor-settings__section-header">
                    <p className="doctor-settings__label">
                        WORKSPACE
                    </p>

                    <h2>Preferences</h2>
                </div>


                <div className="doctor-settings__option">

                    <div>
                        <h3>Notifications</h3>

                        <p>
                            Receive important workspace notifications.
                        </p>
                    </div>

                    <button
                        type="button"
                        className={`settings-toggle ${
                            notifications
                                ? "settings-toggle--active"
                                : ""
                        }`}
                        onClick={() =>
                            setNotifications(!notifications)
                        }
                    >
                        <span />
                    </button>

                </div>


                <div className="doctor-settings__option">

                    <div>
                        <h3>Medication Safety Alerts</h3>

                        <p>
                            Show alerts when reviewing medication safety
                            information.
                        </p>
                    </div>

                    <button
                        type="button"
                        className={`settings-toggle ${
                            safetyAlerts
                                ? "settings-toggle--active"
                                : ""
                        }`}
                        onClick={() =>
                            setSafetyAlerts(!safetyAlerts)
                        }
                    >
                        <span />
                    </button>

                </div>

            </section>


            <section className="doctor-settings__panel">

                <div className="doctor-settings__section-header">
                    <p className="doctor-settings__label">
                        SYSTEM
                    </p>

                    <h2>System Information</h2>
                </div>

                <div className="doctor-settings__system-grid">

                    <div>
                        <span>APPLICATION</span>
                        <strong>NeoGraphMed</strong>
                    </div>

                    <div>
                        <span>VERSION</span>
                        <strong>1.0.0</strong>
                    </div>

                    <div>
                        <span>STATUS</span>
                        <strong className="system-status">
                            ● Online
                        </strong>
                    </div>

                    <div>
                        <span>DATA SCOPE</span>
                        <strong>
                            Medication Safety Dataset
                        </strong>
                    </div>

                </div>

            </section>

        </div>
    );
}

export default Settings;