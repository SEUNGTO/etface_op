<script>
    import { onMount } from "svelte";
    import Chart from "chart.js/auto";

    export let price = {};
    let chart;
    let chartContainer;

    function createChart() {
        const ctx = chartContainer.getContext("2d");
        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: Object.values(price['Date']),
                datasets: [
                    {
                        label: "종가",
                        data: Object.values(price['Close']),
                        yAxisID : 'y1'
                    },
                    {
                        label: "목표가",
                        data: Object.values(price['target']),
                        yAxisID : 'y2'
                    }
                ],
            },
            options: {
                maintainAspectRatio: false,
                interaction : {
                    mode : 'index',
                },
                scales: {
                    y1 : {
                        type : 'linear',
                        display : true,
                        potision : 'left',
                    },
                    y2 : {
                        type : 'linear',
                        display : true,
                        potision : 'right',
                    },

               },
                plugins: {
                    legend: {
                        display: true,
                        position:'top',
                        align:'top',
                    },
                },
            },
        });
    }
    onMount(() => {
        createChart();
    });
</script>

<div>
    <canvas bind:this={chartContainer}></canvas>
</div>

<style>
    canvas {
        height:30vh;
        width:100vw;
        max-height: 30vh;
        max-width: 100%;
        /* position: relative; */
    }

</style>
