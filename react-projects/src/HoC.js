import react from 'react'

export function HoC(component, props){
    return class extends react.Component {
        constructor(props){
            super(props)
            this.state = {}
        }
        render(){
            return (
                <h1>fd</h1>
            )
        }
    }
}

