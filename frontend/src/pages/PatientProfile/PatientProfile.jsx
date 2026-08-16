import { useEffect, useState } from "react";
import {
    getPatientProfile,
    updatePatientProfile,
} from "../../services/patientService";
import "./PatientProfile.css";

function PatientProfile() {
    const [profile, setProfile] = useState({
        name: "",
        patientId: "",
        age: "",
        gender: "",
        condition: "",
    });

    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    // Load logged-in patient's profile from MongoDB
    useEffect(() => {
        const loadProfile = async () => {
            try {
                setLoading(true);
                setError("");

                const response = await getPatientProfile();

                const patient = response.profile;

                setProfile({
                    name: patient.full_name || "",
                    patientId: patient.patient_id || "",
                    age: patient.age ?? "",
                    gender: patient.gender || "",
                    condition: patient.medical_condition || "",
                });

            } catch (profileError) {
                console.error("Unable to load patient profile:", profileError);

                const detail = profileError?.response?.data?.detail;

                setError(
                    detail || "Unable to load patient profile."
                );
            } finally {
                setLoading(false);
            }
        };

        loadProfile();
    }, []);

    const handleChange = (event) => {
        const { name, value } = event.target;

        setProfile((prev) => ({
            ...prev,
            [name]: value,
        }));

        setSaved(false);
        setError("");
    };

    // Save profile to MongoDB
    const handleSave = async (event) => {
        event.preventDefault();

        try {
            setSaving(true);
            setSaved(false);
            setError("");

            const response = await updatePatientProfile(profile);

            console.log("Profile saved:", response);

            // Update screen with the saved data
            const patient = response.profile;

            setProfile({
                name: patient.full_name || "",
                patientId: patient.patient_id || "",
                age: patient.age ?? "",
                gender: patient.gender || "",
                condition: patient.medical_condition || "",
            });

            setSaved(true);

        } catch (saveError) {
            console.error("Profile update failed:", saveError);

            const detail = saveError?.response?.data?.detail;

            setError(
                detail || "Unable to save patient profile."
            );
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="patient-profile">
                <section className="patient-profile__hero">
                    <p className="patient-profile__kicker">
                        PATIENT PROFILE
                    </p>

                    <h1>My Profile</h1>

                    <p>
                        Loading your profile...
                    </p>
                </section>
            </div>
        );
    }

    return (
        <div className="patient-profile">

            {/* Header */}

            <section className="patient-profile__hero">

                <p className="patient-profile__kicker">
                    PATIENT PROFILE
                </p>

                <h1>
                    My Profile
                </h1>

                <p>
                    Manage your personal and medical information.
                </p>

            </section>


            {/* Profile Card */}

            <section className="patient-profile__card">

                <div className="patient-profile__card-header">

                    <div>

                        <span className="patient-profile__label">
                            PERSONAL INFORMATION
                        </span>

                        <h2>
                            Patient Profile
                        </h2>

                        <p>
                            Keep your information up to date for
                            accurate medication management.
                        </p>

                    </div>


                    <div className="patient-profile__avatar">

                        {profile.name
                            ? profile.name.charAt(0).toUpperCase()
                            : "P"}

                    </div>

                </div>


                <form
                    className="patient-profile__form"
                    onSubmit={handleSave}
                >

                    {/* Name */}

                    <label className="patient-profile__field">

                        <span>
                            Full Name
                        </span>

                        <input
                            type="text"
                            name="name"
                            value={profile.name}
                            onChange={handleChange}
                            placeholder="Enter your full name"
                            required
                        />

                    </label>


                    {/* Patient ID */}

                    <label className="patient-profile__field">

                        <span>
                            Patient ID
                        </span>

                        <input
                            type="text"
                            name="patientId"
                            value={profile.patientId}
                            readOnly
                        />

                        <small>
                            Patient ID is assigned by the system.
                        </small>

                    </label>


                    {/* Age */}

                    <label className="patient-profile__field">

                        <span>
                            Age
                        </span>

                        <input
                            type="number"
                            name="age"
                            value={profile.age}
                            onChange={handleChange}
                            min="1"
                            max="120"
                            placeholder="Enter your age"
                            required
                        />

                    </label>


                    {/* Gender */}

                    <label className="patient-profile__field">

                        <span>
                            Gender
                        </span>

                        <select
                            name="gender"
                            value={profile.gender}
                            onChange={handleChange}
                            required
                        >

                            <option value="">
                                Select gender
                            </option>

                            <option value="Male">
                                Male
                            </option>

                            <option value="Female">
                                Female
                            </option>

                            <option value="Other">
                                Other
                            </option>

                        </select>

                    </label>


                    {/* Medical Condition */}

                    <label className="patient-profile__field patient-profile__field--full">

                        <span>
                            Medical Condition
                        </span>

                        <select
                            name="condition"
                            value={profile.condition}
                            onChange={handleChange}
                            required
                        >

                            <option value="">
                                Select medical condition
                            </option>

                            <option value="Type 2 Diabetes">
                                Type 2 Diabetes
                            </option>

                            <option value="Hypertension">
                                Hypertension
                            </option>

                            <option value="Arthritis">
                                Arthritis
                            </option>

                        </select>

                    </label>


                    {/* Error */}

                    {error && (
                        <div className="patient-profile__error">
                            {error}
                        </div>
                    )}


                    {/* Save */}

                    <div className="patient-profile__actions">

                        <button
                            type="submit"
                            className="patient-profile__save"
                            disabled={saving}
                        >

                            {saving
                                ? "Saving..."
                                : "Save Profile"}

                        </button>


                        {saved && (
                            <span className="patient-profile__saved">
                                ✓ Profile saved
                            </span>
                        )}

                    </div>

                </form>

            </section>

        </div>
    );
}

export default PatientProfile;