style: """
    width: 100%;
    margin-top: 0;
    margin-left: 0;
    left: 0;
    bottom: -3px;
    padding: 0;
    border: 0 solid #222;
    -webkit-user-select: none;
    user-select: none;


    div.outer {
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
        border-right: 1px solid gray;
    }

    img.icon {
        height: 34px;
        width: 38px;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: calc(-10px);
    }

    div.line {
        position: relative;
        height: 5px;
        border-top: 1px solid gray;
    }

    div.line-right {
        bottom: 10px;
        left: 85px;
    }

    div.line-right-straight {
        width: 58px;
    }

    div.line-right-angle {
        width: 45px;
        border-right: 1px solid gray;
    }

    div.line-left {
        top: 24px;
    }

    div.line-left-angle {
        right: 38px;
        width: 75px;
        border-left: 1px solid gray;
    }

    div.line-left-straight {
        width: 38px;
        left: 0px;
    }

    div.desktop {
        position: relative;
        right: 70px;
        top: 33px;
    }

    div.desktop-hide {
        display none;
    }

    div.desktop-show {
        font-size: 14px;
        font-family: SFNS Display, 'Andale Mono', sans-serif;
        color: gray;
    }


"""

command: "/usr/local/bin/python3 ./windows/neaty.py --monitor 1"

refreshFrequency: 1000

render: ->
  """
    <div class='outer'>
        <table id="table">
            <tr id="toprow"> </tr>
            <tr id="botrow"> </tr>
        </table>
    </div>
    """

update: (output, domEl) ->
  try
    info = JSON.parse(output)
  catch error
    console.log("Python Error:")
    console.log(output)
    $(domEl).text(output)
    return # to debug errors in python code

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
    w = info[i]
    if 2 * i >= toprow.children('td').length
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


    if cell_name.attr("title") != w["title"]
      console.log("update this monitor")
      cell_name.attr("title", w["title"])
      cell_number.text(w["no"] % 10)
      cell_name.text(w["short"])
      cell_icon.append($("<div id='desktop-no#{i}'>"))
      cell_icon.append($("<div id='line-left#{i}'>"))
      cell_icon.append($("<img class='icon' src='#{w["icon"]}' id='img#{i}'>"))
      cell_icon.append($("<div id='line-right#{i}'>"))

    window_no = "window#{w['no']}"
    if !cell_number.attr("class").includes(window_no)
      console.log("update numbers (there was only a change on a different monitor")
      cell_name.attr("class", "name #{window_no} #{'lastname' if w['last'] && i != info.length - 1}")
      cell_icon.attr("class", "icon #{window_no}")
      cell_number.attr("class", "no #{window_no} #{'firstno' if w['first']}")
      cell_number.text(w['no'] % 10)
      for o in [$(domEl).find("#img#{i}"), cell_number, cell_name, cell_icon]
        o.on("click", calls[w['no']])
      $(domEl).find("#line-left#{i}").attr("class",
        "line line-left #{if w['first'] then 'line-left-angle' else 'line-left-straight'}")
      $(domEl).find("#line-right#{i}").attr("class",
        "line line-right #{if w['last'] then 'line-right-angle' else 'line-right-straight'}")
      $(domEl).find("#desktop-no#{i}").text(w['desktop']).attr("class",
        "desktop #{if w['first'] then 'desktop-hide' else 'desktop-show'}")

  for i in [info.length ... toprow.children('td').length]
    $(domEl).find("#no#{i}").remove()
    $(domEl).find("#icon#{i}").remove()
    $(domEl).find("#name#{i}").remove()
