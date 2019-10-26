style: """
    width: 100%;
    margin-top: 0;
    margin-left: 0;
    left: 0;
    bottom: -3px;
    padding: 0;
    border: 0 solid #222;

    div {
        background-image: url(windows/icons/gradient.png);
        width: 100%;
    }


    table {
        margin: 0 auto;
    }

    td {
        padding: 0;
        margin: 0;

        text-align: center;
        vertical-align: bottom;
        color: black;
        text-shadow: white 0px 0px 10px;
    }

    td.no {
        width: 30px;
        text-align: right;
        font-size: 24px;
        font-family: SFNS Display, 'Andale Mono', sans-serif;
    }

    td.firstno {
        width: 80px;
    }


    td.icon {
        height: 40px;
        width: 100px;
        padding-right: 10px;
    }

    td.name {
        width: 120px;
        font-size: 14px;
        font-family: Futura, Helvetica, sans-serif;
        white-space: nowrap;
        padding-right: 10px
    }

    td.lastname {
        border-right: 1px solid;
    }

    img.icon {
        height: 34px;
        width: 38px;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: calc(-10px)
    }
"""

command: "/usr/local/bin/python3 ./windows/neaty.py --monitor 3"

refreshFrequency: 1000

render: ->
    """
    <div id='outer'>
        <table id="table">
            <tr id="toprow"> </tr>
            <tr id="botrow"> </tr>
        </table>
    </div>
    """

update: (output, domEl) ->
    info = JSON.parse(output)
    focus_call = "/usr/local/bin/python3 ./windows/neaty.py --focus "
    calls = {
        1: => @run(focus_call + 1),
        2: => @run(focus_call + 2),
        3: => @run(focus_call + 3),
        4: => @run(focus_call + 4),
        5: => @run(focus_call + 5),
        6: => @run(focus_call + 6),
        7: => @run(focus_call + 7),
        8: => @run(focus_call + 8),
        9: => @run(focus_call + 9),
        10: => @run(focus_call + 10),
    }

    toprow = $(domEl).find('#toprow')
    botrow = $(domEl).find('#botrow')

    for i in [0 ... info.length]
        if 2 * i >=  toprow.children('td').length
            cell_number = $("<td rowspan='2' class='no' id='no#{i}'>")
            cell_icon = $("<td class='icon' id='icon#{i}'>")
            cell_name = $("<td class='name' id='name#{i}'>")
            toprow.append(cell_number)
            toprow.append(cell_icon)
            botrow.append(cell_name)
        else
            cell_number = $(domEl).find("#no#{i}")
            cell_icon = $(domEl).find("#icon#{i}")
            cell_name = $(domEl).find("#name#{i}")


        if cell_name.attr("title") != info[i]["title"]
            console.log("update this monitor")
            cell_name.attr("title", info[i]["title"])
            cell_number.text(info[i]["no"]%10)
            cell_name.text(info[i]["short"])
            cell_icon.html($("<img class='icon' src='#{info[i]["icon"]}' class='icon' id='img#{i}'>"))

        window_no = "window#{info[i]['no']}"
        if !cell_number.attr("class").includes(window_no)
            console.log("update numbers (there was only a change on a different monitor")
            cell_name.attr("class", "name #{window_no} #{'lastname' if info[i]['last'] && i != info.length-1}")
            cell_icon.attr("class", "icon #{window_no}")
            cell_number.attr("class", "no #{window_no} #{'firstno' if info[i]['first']}")
            cell_number.text(info[i]['no'] % 10)
            for o in [$(domEl).find("#img#{i}"), cell_number, cell_name, cell_icon]
                o.on("click", calls[info[i]['no']])

    for i in [info.length ... toprow.children('td').length]
        $(domEl).find("#no#{i}").remove()
        $(domEl).find("#icon#{i}").remove()
        $(domEl).find("#name#{i}").remove()

###
