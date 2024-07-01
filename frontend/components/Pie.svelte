<script>
    import { onMount } from "svelte";
    import Chart from "chart.js/auto";

    export let top10 = {};
    let chart;
    let chartContainer;

    function createChart() {
        const ctx = chartContainer.getContext("2d");
        chart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: Object.keys(top10),
                datasets: [
                    {
                        label: "보유 종목별 비중",
                        data: Object.values(top10),
                        hoverOffset: 50,
                    },
                ],
            },
            options: {
                scales: {
                },
                plugins: {
                    legend: {
                        display: true,
                        position:'right',
                        align:'right',
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
        max-width: 100%;
        max-height: 100%;
    }
</style>
