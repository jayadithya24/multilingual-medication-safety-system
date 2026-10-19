import "./StatsSection.css";

function StatsSection() {

    const stats = [
        {
            number: "100",
            title: "English medicines · 10 diseases"
        },
        {
            number: "3",
            title: "Languages"
        },
        {
            number: "100 each",
            title: "Kannada & Tulu medicines · 10 diseases each"
        },
        {
            number: "Rule-Based",
            title: "Safety Monitoring"
        }
    ];

    return (

        <section className="stats">

            <h2>System Statistics</h2>

            <div className="stats-grid">

                {stats.map((item,index)=>(

                    <div className="stat-card" key={index}>

                        <h1>{item.number}</h1>

                        <p>{item.title}</p>

                    </div>

                ))}

            </div>

        </section>

    );

}

export default StatsSection;
