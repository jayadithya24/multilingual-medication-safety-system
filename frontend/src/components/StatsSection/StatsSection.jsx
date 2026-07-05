import "./StatsSection.css";

function StatsSection() {

    const stats = [
        {
            number: "1000+",
            title: "Medicines"
        },
        {
            number: "12+",
            title: "Languages"
        },
        {
            number: "500+",
            title: "Drug Interactions"
        },
        {
            number: "99%",
            title: "Accuracy"
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