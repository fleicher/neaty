style:
    """    width: 100%; bottom: -3px; user-select: none;
    """ + require('fs').readFileSync "/Users/leichef/Library/Application Support/Übersicht/widgets/windows/style.css", "utf8"

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
      div_desktop = $("<div id='desktop-no#{i}'>")
      div_line_left = $("<div id='line-left#{i}'>")
      img_icon = $("<img class='icon' src='#{w["icon"]}' id='img#{i}'>")
      div_line_right = $("<div id='line-right#{i}'>")
      cell_icon.append(div_desktop)
      cell_icon.append(div_line_left)
      cell_icon.append(img_icon)
      cell_icon.append(div_line_right)

    else
      cell_number = $(domEl).find("#no#{i}")
      cell_icon = $(domEl).find("#icon#{i}")
      cell_name = $(domEl).find("#name#{i}")
      div_desktop = $(domEl).find("#desktop-no#{i}")
      div_line_left = $(domEl).find("#line-left#{i}")
      img_icon = $(domEl).find("#img#{i}")
      div_line_right = $(domEl).find("#line-right#{i}")

    if cell_name.attr("title") != w["title"]
      console.log("update this monitor")
      cell_name.attr("title", w["title"])
      cell_number.text(w["no"] % 10)
      cell_name.text(w["short"])
      img_icon.attr("src", "#{w['icon']}")

    window_no = "window#{w['no']}"
    if !cell_number.attr("class").includes(window_no)
      console.log("update numbers (there was only a change on a different monitor")
      cell_name.attr("class", "name #{window_no} #{'lastname' if w['last'] && i != info.length - 1}")
      cell_icon.attr("class", "icon #{window_no}")
      cell_number.attr("class", "no #{window_no} #{'firstno' if w['first']}")
      cell_number.text(w['no'] % 10)
      for o in [$(domEl).find("#img#{i}"), cell_number, cell_name, cell_icon]
        o.on("click", calls[w['no']])
      div_line_left.attr("class",
        "line line-left #{if w['first'] then 'line-left-angle' else 'line-left-straight'}")
      div_line_right.attr("class",
        "line line-right #{if w['last'] then 'line-right-angle' else 'line-right-straight'}")
      div_desktop.text(w['desktop']).attr("class",
        "desktop #{if w['first'] then 'desktop-hide' else 'desktop-show'}")

  for i in [info.length ... toprow.children('td').length]
    $(domEl).find("#no#{i}").remove()
    $(domEl).find("#icon#{i}").remove()
    $(domEl).find("#name#{i}").remove()
    $(domEl).find("#line-left#{i}").remove()
    $(domEl).find("#line-right#{i}").remove()
    $(domEl).find("#desktop-no#{i}").remove()
