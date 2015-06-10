// (c) Copyright 2015, Synapse Wireless, Inc.
// Main javascript file for Sensors Demo

var blast_img;

// Document Loaded callback
$(document).ready(function() {
    wsHub.start();
    initCharts();
    initBlasters();
    
    blast_img = new Image();
    blast_img.src = 'Iron-Man-Hand.png';
    
    console.log("hello!");
});

// Call-in from server SNAP application
function report_dist(index, val) {
    plot(index, val);
    if (val > 100) {
        val = 100;
    }
    set_blast(index, val);
}

var blasters = Array();

function initBlasters()  {
    var index;
    for	(index = 0; index < 4; index++) {
        blaster = createBlaster(index);
        blasters.push(blaster);
    }
}

function createBlaster(index) {
    var c = document.getElementById("blast_canvas" + index);
    var ctx = c.getContext("2d");
    return ctx;
}

function set_blast(index, val) {
    // val is 0-100% of "ray" blast
    
    var y_tri, y_g1, y_g2;
    y_tri = 75 + 600 * val / 100.0;
    y_g1 = 75;
    y_g2 = 800;

    // Get context, and draw base image
    var ctx = blasters[index];
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);    
    ctx.drawImage(blast_img,10,10, 300, 400);  // x, y, width, height
    
    // Create "ray" gradient
    var grd=ctx.createRadialGradient(205,y_g1,125,205,y_g2,350);
    grd.addColorStop(0.3,"#0099ff");
    grd.addColorStop(0.6,"white");
    grd.addColorStop(1,"black");
    
    // Draw triangular shape
    ctx.beginPath();
    ctx.moveTo(205, 75);
    ctx.lineTo(20, y_tri);
    ctx.lineTo(390, y_tri);
    ctx.closePath();

    // Fill with gradient
    ctx.fillStyle=grd;    
    ctx.fill();
}

// Plot a new point
function plot(chart_num, val)  {
    var chart = light_charts[chart_num];
    var series = chart.series[0];
    
    var time = (new Date()).getTime();
    var shift = series.data.length > 20; // shift if the series is longer than 20

    // add the point
    series.addPoint({x:time, y:val}, true, shift);
}


// HighCharts "strip charts"
var light_charts = Array();

function initCharts()  {
    var index;
    for	(index = 0; index < 4; index++) {
        chart = createChart(index);
        light_charts.push(chart);
    }
}

function createChart(num)  {
    var light_chart;
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    light_chart = new Highcharts.Chart({
        chart: {
            renderTo: 'dist_plot' + num,
            defaultSeriesType: 'spline',
            marginRight: 10,
            events: {
                load: function() {
                }
            }
        },
        title: {
            text: 'Distance'
        },
        xAxis: {
            type: 'datetime',
            tickPixelInterval: 150
        },
        yAxis: {
            max: 200,
            min: 0,
            tickInterval: 12,
            title: {
                text: 'Inches'
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        legend: {
            enabled: false
        },
        exporting: {
            enabled: false
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            // Disable fancy features to optimize for CPU-challenged systems
            series: {
                enableMouseTracking: false,
                animation: false,
                marker: {
                    enabled: false
                }
            }
        },
        series: [{
            name: 'Distance',
            data: []
        }]
    });
    return light_chart;
}

