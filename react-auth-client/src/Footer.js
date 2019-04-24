import React from 'react'
import FontAwesome from 'react-fontawesome'

export default () => {
  return (
    <footer>
      <a 
        href='https://github.com/icnyts/CS-411-Project' 
        title='Our Fancy Github repo' // only reason to put github here is the bottom is too empty
        className={'github'}
      >
        <FontAwesome
          name={'github'}
        />
      </a>
    </footer>
  )
}