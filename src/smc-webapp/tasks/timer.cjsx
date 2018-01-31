###
Stopwatch for timing a particular task
###

{Stopwatch} = require('../editor_time')

{React, rclass, rtypes}  = require('../smc-react')

exports.Timer = rclass
    propTypes :
        actions   : rtypes.object
        task_id   : rtypes.string.isRequired
        read_only : rtypes.bool

    shouldComponentUpdate: (next) ->
        return @props.task_id   != next.task_id  or \
               @props.read_only != next.read_only

    render_none: ->
        <span style={color:'#888'}>
            none
        </span>

    click: (args...) ->
        console.log 'click', args

    render_stopwatch: ->
        <Stopwatch
            label        = {''}
            total        = {0}
            state        = {'running'}
            time         = {new Date() - 0}
            click_button = {@click}
            compact      = {true}
        />

    render: ->
        <div style={marginBottom: '5px', fontSize: '10pt'}>
            {@render_stopwatch()}
        </div>
