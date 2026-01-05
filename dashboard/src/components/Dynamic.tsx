import React, { Suspense } from 'react';  

import { currentUserToken } from "./auth/auth0-provier-with-history"; 

import { useAuth0 } from '@auth0/auth0-react'; 

const DynamicComponent = (props: any) => {

  

  // const [customer, setCustomer] = useState({ customerId }); 

  const { isAuthenticated, user, isLoading } = useAuth0(); 

  const loadScope = (url: any, scope: any) => {

    const element = document.createElement('script'); 

    const promise = new Promise((resolve, reject) => {

      element.src = url; 

      element.type = 'text/javascript'; 

      element.async = true; 

      element.onload = () => resolve(window[scope]); 

      element.onerror = reject; 

    }); 

    document.head.appendChild(element); 

    promise.finally(() => document.head.removeChild(element)); 

    return promise; 

  }; 

  const loadModule = async (url: any, scope: any, module: any) => {

    try { 

      const container: any = await loadScope(url, scope); 

      await __webpack_init_sharing__('default'); 

      await container.init(__webpack_share_scopes__.default); 

      const factory = await container.get(module); 

      return factory(); 

    } catch (error) { 

      console.error('Error loading module:', error); 

      throw error; 

    } 

  }; 

  

  // Wait for auth to finish loading
  if (isLoading) {
    return (
      <div className="parentDisable">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading authentication...</span>
        </div>
        <div className="loader mt-2 text-muted">Loading authentication...</div>
      </div>
    );
  }

  // Check if authenticated
  if (!isAuthenticated) {
    return (
      <div className="parentDisable">
        <div className="text-muted">Please log in to continue</div>
      </div>
    );
  }

  // Only load the module after auth is ready
  const MFComp = React.lazy(() => { 

    return loadModule( 

      props.data.componentURL || props.data.url, 

      props.data.componentName, 

      props.data.componentClass, 

    ); 

  }); 

  

  // const setCustomerId = (id) => { 

  //   setCustomer({ customerId: id }); 

  // }; 

  

  return ( 

    <Suspense 

      fallback={ 

        <div className="parentDisable" > 

          <div className="spinner-border text-primary" role="status"> 

            <span className="visually-hidden">Loading...</span> 

          </div> 

          <div className="loader mt-2 text-muted">Loading</div> 

        </div> 

      } 

    > 

        <MFComp 

          data={props} 

            currentUserToken={currentUserToken} 

        ></MFComp> 

        {/* {props.data.componentName} */} 


    </Suspense> 

  ); 

};

  

export default DynamicComponent; 