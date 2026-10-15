import "./Loading.css";

function Loading() {
  return (
    <div className="loading-container">
      <div className="loader"></div>

      <h3>Scanning Medicine...</h3>

      <p>Please wait while our AI detects the medicine.</p>
    </div>
  );
}

export default Loading;