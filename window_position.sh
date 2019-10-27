#!/bin/bash
if [ "$1" = "" ]; then
  process="Google Chrome"
  echo "Parameter empty, set it to '$process'"
else
  process="$1"
fi

osascript << EOF
tell application "System Events"
	set myresult to item 1 of {({position, title} of every window of application process "$process")}
	-- myresult is a fake list
	-- log myresult
	set mypositions to (item 1 of myresult)
	set mytitles to (item 2 of myresult)
	set AppleScript's text item delimiters to {return & linefeed, return, linefeed, character id 8233, character id 8232}
  set output to ""
--	set output to "{
--"
	set counter to 0
	repeat with myposition in mypositions
		set counter to counter + 1
		set mytitle to text items of ((item counter of mytitles) as string)
		-- replacing line breaks in title with space
		set AppleScript's text item delimiters to {" "}
		set mytitle to mytitle as text
		if mytitle is not equal to "" then
			--set output to output & "    "
			set output to output & "[" & item 1 of myposition & ", " & item 2 of myposition & "]"
			set output to output & ":@: " & mytitle & "
"
		end if
	end repeat
--	set output to (text 1 thru -3 of output) & "
--}"
	return output
end tell
EOF

# this script will automatically create a popup so that the
# Ubersicht app can ask for permissions to "System Events"
