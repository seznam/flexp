$(function(){

    /* Toggle content matching title */
    $(".toggle").click(function(){
        $("." + $(this).attr("data-toggle")).slideToggle();
    });

    /* Toggle content matching title */
    $(".toggle-cookie").click(function(){
        var element_toggle_class = $(this).attr("data-toggle");
        var element =  $("." + element_toggle_class);
        var visible = element.is(":visible");
        set_cookie(element_toggle_class, !visible);
        show_element(element, !visible);
        set_button_class($(this), !visible);
    });

    $(".toggle-cookie").each(function(){
            var element_toggle_class = $(this).attr("data-toggle");
            var element =  $("." + element_toggle_class);
            var show = get_cookie(element_toggle_class, true);
            show_element(element, show);
            set_button_class($(this), show);
        }
    )

    $('table.tr-link tr').click(function(){
        href = $(this).attr('data-href');
        if (href){
            window.location = href
            return false;
        }
    });

    $( "#dialog-confirm" ).dialog({
      resizable: false,
      height: "auto",
      width: 400,
      modal: true,
      autoOpen: false,
      buttons: {
        "Delete": function() {
            var folder = $(this).data('folder');
            $.post("/ajax", {action: "delete_folder", value: folder}, function(){
                location.reload();
            });
            $( this ).dialog( "close" );
        },
        Cancel: function() {
          $( this ).dialog( "close" );
        }
      }
    });

    $( "#dialog-rename" ).dialog({
      resizable: false,
      height: "auto",
      width: 400,
      modal: true,
      autoOpen: false,
      buttons: {
        "Rename": rename,
        Cancel: function() {
          $( this ).dialog( "close" );
        }
      }
    });

    $( "#dialog-rename form" ).on( "submit", function( event ) {
      event.preventDefault();
      rename();
    });


    $( "#edit-txt" ).dialog({
      resizable: false,
      height: "auto",
      width: 500,
      modal: true,
      autoOpen: false,
      buttons: {
        "Replace content": edit_txt,
        Cancel: function() {
          $( this ).dialog( "close" );
        }
      }
    });

    $( "#edit-txt form" ).on( "submit", function( event ) {
      event.preventDefault();
      edit_txt();
    });

    width = get_cookie("sidenav_width", "300px");
    resize_main(width);

});

function show_element(element, show){
    if (show){
        element.slideDown();
    } else {
        element.slideUp()
    }
}

function set_button_class(element, show){
    var class_off = element.attr("data-class-off");
    if (show){
        element.removeClass(class_off);
    } else {
        element.addClass(class_off);
    }
}

function edit_txt(){
        dialog = $( "#edit-txt" );
        var new_content = dialog.find("#new_content").val();
        var file_name = dialog.data("file_name");
        var folder = dialog.data('folder');
        $.post("/ajax", {action: "change_file_content", value: folder, file_name:file_name, new_content:new_content})
            .done(function(){
                var url = location.href;
                if (url.endsWith(folder)){
                    url = url.replace(folder, new_name);
                }
                location.href = url;
            })
            .fail(function(xhr, status, error){
                alert(error)
            });
        dialog.dialog( "close" );
}

function rename(){
        dialog = $( "#dialog-rename" );
        var new_name = dialog.find("#new_name").val();
        var folder = dialog.data('folder');
        $.post("/ajax", {action: "rename_folder", value: folder, new_name:new_name})
            .done(function(){
                var url = location.href;
                if (url.endsWith(folder)){
                    url = url.replace(folder, new_name);
                }
                location.href = url;
            })
            .fail(function(xhr, status, error){
                alert(error)
            });
        dialog.dialog( "close" );
    }

function nav_onresize(){
    var width = $("#sidenav").css("width");
    set_cookie("sidenav_width", width);
    resize_main(width);
}

function resize_main(width){
    $("#main").css("margin-left", width);
    $("#footer").css("margin-left", width);
    $("#sidenav").css("width", width);
}

function set_cookie(key, val){
    document.cookie = key+"="+JSON.stringify(val);
}

function get_cookie(name, def) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return JSON.parse(c.substring(nameEQ.length,c.length));
    }
    return def;
}


$(document).ready(function()
    {
        $(".tablesorter").each(function()
        {
            $(this).tablesorter();
        });

    }
);


function d3ize(where, x, ydata) {
    d3ize_table(where, x, ydata);
    d3ize_plot(where, x, ydata);
    d3.select(where).append("br").style("clear", "both");
}


function identity(x) {return x}


function d3ize_table(selector, xdata, ydata) {
    var table = d3.select(selector).append("table")
                  .attr("style", "float: left")
                  .attr("class", "w3-table w3-bordered w3-striped w3-border w3-hoverable w3-card-2"),
        thead = table.append("thead").append("tr").attr("class", "w3-green"),
        tbody = table.append("tbody"),
        rows = null,
        cells = null;

    for (column in xdata) {
        rows = tbody.selectAll("tr")
                .data(xdata[column])
                .enter()
                .append("tr");

        thead.append("th").text(column);
        // add one TD to every TR with value on the proper index
        rows.append("td")
                .html(function(d, i) {return xdata[column][i];});
    }

    for (column in ydata) {
        // prepare min, max value to highlight
        var min_val = d3.min(ydata[column]);
        var max_val = d3.max(ydata[column]);
        console.log("min_val: " + min_val);
        // add header for the column into THEAD TR
        thead.append("th").text(column);
        // add one TD to every TR with value on the proper index
        rows.append("td")
                .html(function(i) {
                    if ((min_val == ydata[column][i-1]) || (max_val == ydata[column][i-1]))
                    {
                        return "<strong>" + ydata[column][i-1] + "</strong>";
                    }
                    else
                    {
                        return ydata[column][i-1];
                    }});
    }
}


function d3ize_plot(selector, xdata, ydata) {

    // Set the dimensions of the canvas / graph
    var margin = {top: 30, right: 50, bottom: 50, left: 50},
        width = 800 - margin.left - margin.right,
        height = 600 - margin.top - margin.bottom;

    var xname = "";

    // Parse the date / time
    //var parseDate = d3.time.format("%d-%b-%y").parse;
    //var formatTime = d3.time.format("%e %B");
    for (xcol in xdata) {
        xname = xcol;
        xvalues = xdata[xcol];
    }

    for (column in ydata) {
        var x = d3.scale.linear()
            .domain([xvalues[0], xvalues[xvalues.length-1]])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([d3.min(ydata[column]), d3.max(ydata[column])])
            .range([height, 0]);

        // Define the line
        var valueline = d3.svg.line()
            .x(function(d, i) { return x(xvalues[i]); })
            .y(function(d, i) { return y(d); });

        // Define the axes
        var xAxis = d3.svg.axis().scale(x)
            .orient("bottom").ticks(15);

        var yAxis = d3.svg.axis().scale(y)
            .orient("left").ticks(15);

        // Define the div for the tooltip
        var div = d3.select(selector).append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // Adds the svg canvas
        var svg = d3.select(selector)
            .append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .attr("class", "chart")
            .append("g")
                .attr("transform",
                      "translate(" + margin.left + "," + margin.top + ")");

        svg.append("text")
            .attr("x", x(xvalues[parseInt(xvalues.length / 2)]))
            .attr("y", y(d3.max(ydata[column])))
            .attr("class", "legend")
            .text(function(d) { return column; });

        // Add the valueline path.
        svg.append("path")
            .attr("class", "line")
            .attr("d", valueline(ydata[column]));

        // Add the scatterplot
        svg.selectAll("dot")
            .data(ydata[column])
        .enter().append("circle")
            .attr("r", 5)
            .attr("cx", function(d, i) { return x(xvalues[i]); })
            //.attr("cy", function(d) { return y(d.loss); })
            .attr("cy", function(d, i) { return y(d); })
            .style("fill", "green")
            .on("mouseover", function(d, i) {
                div.transition()
                   .duration(200)
                   .style("opacity", .9);
                //div .html(d.iter + "<br/>" + d.loss)
                div.html("x=" + xvalues[i] + "<br/>" + column + "=" + d)
                   .style("left", (d3.event.pageX) + "px")
                   .style("top", (d3.event.pageY - 28) + "px");
                })
            .on("mouseout", function(d, i) {
                div.transition()
                    .duration(500)
                    .style("opacity", 0);
            });

        // Add the X Axis
        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        // Add the Y Axis
        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);
    }
}


function d3ize_lameplot(data) {

    // create a boxplot for every column
    var x = d3.scale.linear()
            .domain([d3.min(data[column]), d3.max(data[column])])
            .range([0, 470]);

    var divw = parseInt(600 / data[column].length);

    for (column in data) {
        d3.select("#content")
            .append("div")
                .attr("class", "chart")
                .text(function() {return column;})
            .selectAll("div")
                .data(data[column])
                .enter().append("div")
                    .style("width", function(d, i) { return divw + "px"; })
                    .style("height", function(d, i) { return parseInt(x(d)) + "px"; })
                    .style("left", function(d, i) { return divw * i + "px"; });
    }
}
