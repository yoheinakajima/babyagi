
import React from 'react';

class ListComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      items: props.items
    };
  }

  render() {
    return (
      <div>
        { this.state.items.map(item => <div>{item}</div>)}
      </div>
    );
  }
}

export default ListComponent;