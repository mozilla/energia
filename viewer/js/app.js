"use strict"

if (typeof String.prototype.endsWith != 'function') {
  String.prototype.endsWith = function(suffix) {
      return this.indexOf(suffix, this.length - suffix.length) !== -1;
  };
}

if (typeof String.prototype.startsWith != 'function') {
  String.prototype.startsWith = function (str){
    return this.indexOf(str) == 0;
  };
}

google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);
window.onresize = drawChart

function drawChart() {
  var ds = new Miso.Dataset({
    url : "/data/report.csv",
    delimiter : ","
  });

  ds.fetch({
    success: function(){
      loadToolbar(ds);
      sort(ds);
      ds = select(ds);
      plotMetrics(ds)
    }
  });
}

function loadToolbar(ds) {
  document.getElementById('limitPicker').onchange = function() {
    document.getElementById('body').innerHTML = "";
    drawChart();
  }

  var picker = setupScrollPicker();
  var sorter = setupSortPicker();

  if (picker.childNodes.length > 0 && sorter.childNodes.length > 0)
    return;

  addOptionToPicker(picker, "");

  ds.eachColumn(function(columnName, column, index){
    if (columnName != "X" && !columnName.endsWith("CI") &&
        columnName != "Page" && columnName != "Browser" &&
        columnName != "OS" && !columnName.endsWith("Impact") &&
        columnName != "Iterations" && columnName != "Duration") {
      addOptionToPicker(picker, columnName);
      addOptionToPicker(sorter, columnName);
    }
  });
}

function setupScrollPicker() {
  var select = document.getElementById('columnPicker');

  select.onchange = function(e) {
    if (e.target.selectedIndex == 0)
      return;

    var el = document.getElementsByClassName("chart")[0];
    var width = parseInt(getComputedStyle(el).getPropertyValue("width"));
    window.scrollTo(width * (e.target.selectedIndex - 1), document.documentElement.scrollTop);
  }

  window.onscroll = function(e) {
    select.selectedIndex = 0;
  }

  return select;
}


function setupSortPicker() {
  var select = document.getElementById('sortPicker');
  select.onchange = function(e) {
    drawChart();
  }

  return select;
}

function addOptionToPicker(picker, columnName) {
  var option = document.createElement("option");
  option.innerHTML = columnName;
  picker.appendChild(option);
}

function sort(ds) {
  var enumeration = {};
  var picker = document.getElementById("sortPicker");
  var sortColumn = picker.options[picker.selectedIndex].text;
  var pvalues = pvaluesForColumn(ds, sortColumn);

  ds.each(function(row, index){
    enumeration[row._id] = index;
  });

  ds.sort(function(rowA, rowB) {
    var rowApvalue = pvalues[enumeration[rowA._id]];
    var rowBpvalue = pvalues[enumeration[rowB._id]];

    if (!isNaN(rowApvalue)) {
      // sort by pvalue
      if (rowApvalue * rowBpvalue < 0) {
        return (rowApvalue > 0) ? -1 : 1
      }

      if (rowApvalue > rowBpvalue) {
        return 1;
      }

      if (rowApvalue < rowBpvalue) {
        return -1;
      }
    } else {
      console.log("Warning: pvalue sorting not possbile due to missing data")
    }

    // sort by page
    if (rowA.Page > rowB.Page) {
      return 1;
    }

    if (rowA.Page < rowB.Page) {
      return -1;
    }

    // sort by browser name
    if (rowA.Browser > rowB.Browser) {
      return 1;
    }

    if (rowA.Browser < rowB.Browser) {
      return -1;
    }

    return 0;
  });
}

function pvaluesForColumn(ds, column) {
  var browsers = ds.countBy('Browser').toJSON();
  var nBrowsers = browsers.length;
  var ffIndex = -1;
  var pvalues = [];

  for (var i in browsers) {
    if (browsers[i]['Browser'].startsWith("Firefox")) {
      ffIndex = parseInt(i);
      break;
    }
  }

  ds.each(function(row, index) {
    var zeroThreshold = 0.001;

    if (index % nBrowsers == 0) {
      var nSamples = row["Iterations"];
      var i = index + ffIndex;
      var ffRow = ds.rowByPosition(i);
      var ffMean = ffRow[column];
      var ffCI = ffRow[column + " CI"];
      var ffSd = Math.max(stdFromMeanCI(ffMean, ffCI, nSamples), zeroThreshold);

      var pvaluePos = Number.MAX_VALUE;
      var pvalueNeg = Number.MAX_VALUE;

      for (var browserIndex = 0; browserIndex < nBrowsers;  browserIndex++) {
        if(browserIndex == ffIndex)
          continue;

        var j = index + browserIndex;
        var browserRow = ds.rowByPosition(j);
        var browserMean = browserRow[column];
        var browserCI = browserRow[column + " CI"];
        var browserSd = Math.max(stdFromMeanCI(browserMean, browserCI, nSamples), zeroThreshold);

        var pv = Math.max(jStat.ttest(browserMean, ffMean, ffSd, nSamples, 2),
                          jStat.ttest(ffMean, browserMean, browserSd, nSamples, 2));

        if (ffMean < browserMean) {
          pvalueNeg = Math.min(pv, pvalueNeg);
        } else {
          pvaluePos = Math.min(pv, pvaluePos);
        }
      }

      if (pvaluePos != Number.MAX_VALUE)
        pvalues.push(pvaluePos);
      else
        pvalues.push(-pvalueNeg);
    } else {
      pvalues.push(pvalues[pvalues.length - 1]);
    }
  });

  return pvalues;
}

function stdFromMeanCI(mean, CI, n) {
  //TODO: *assuming* 95% CI
  var tvalue = jStat.studentt.inv(0.975, (n - 1));
  var sem = CI/tvalue;
  return Math.sqrt(n)*sem;
}

function select(ds) {
  var browsers = ds.countBy('Browser').toJSON();
  var nbrowsers = browsers.length;
  var picker = document.getElementById('limitPicker');
  var max = parseInt(picker.options[picker.selectedIndex].text) * nbrowsers;
  var index = 0;

  if (isNaN(max))
    return ds;

  ds = ds.rows(function(row) {
    return index++ < max;
  });

  return ds;
}

function plotMetrics(ds) {
  var i = 0;
  var nsamples = ds.rowByPosition(0)['Iterations'];

  ds.eachColumn(function(columnName, column, index){
    if (columnName != "X" && !columnName.endsWith("CI") &&
        columnName != "Page" && columnName != "Browser" &&
        columnName != "OS" && !columnName.endsWith("Impact") &&
        columnName != "Iterations" && columnName != "Duration") {
      var df = convertData(ds, columnName)
      var div = createChartContainer(i);
      plot(ds, df, div, columnName);
      i++;
    }
  });
}

function createChartContainer(index) {
  var div = document.createElement('div');
  div.className = 'chart'
  div.style.left = (index * 450) + 'px';
  document.getElementById('body').appendChild(div)
  return div;
}

function convertData(ds, plot_column) {
  var browsers = ds.countBy('Browser').toJSON();
  var nbrowsers = browsers.length;
  var plot_column_ci = plot_column + " CI"

  var res = []
  var partial = []

  ds.each(function(row, index){
    if (index == 0) {
      partial.push(row.Page)
    }else if (index % nbrowsers == 0) {
      partial = []
      partial.push(row.Page)
    }

    var base = row[plot_column];
    var ci = row[plot_column_ci];

    partial.push(base);
    partial.push(base - ci);
    partial.push(base + ci);

    if (index % nbrowsers == nbrowsers - 1) {
      res.push(partial);
    }
  });

  return res;
}

function plot(ds, df, chart, title) {
  var browsers = ds.countBy('Browser').toJSON();
  var nbrowsers = browsers.length;
  var size = nbrowsers * df.length * 50;
  var data = new google.visualization.DataTable();

  chart.style.height = size + "px";

  data.addColumn('string', 'Browser'); // Implicit domain column.
  for (var i in browsers) {
    data.addColumn('number', browsers[i]["Browser"])
    data.addColumn({type:'number', role:'interval'});
    data.addColumn({type:'number', role:'interval'});
  }

  data.addRows(df);
  var options = {title: title,
                 fontSize: 12,
                 legend: {position: 'none'},
                 chartArea:{top:30, left:150, height:66*df.length},
                 bar: {groupWidth: '67%'} };
  var chart = new google.visualization.BarChart(chart);
  chart.draw(data, options);
}
