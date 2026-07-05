import "./Loading.css";

function Loading() {
    return (
        <div className="loading-container">
            <div className="spinner"></div>
            <p>Scanning medicine image...</p>
        </div>
    );
}

export default Loading;