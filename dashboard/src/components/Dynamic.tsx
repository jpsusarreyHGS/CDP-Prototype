import React, { Suspense } from 'react';  
import { currentUserToken } from "./auth/auth0-provier-with-history"; 
import { useAuth0 } from '@auth0/auth0-react'; 

// Fallback component when MFE fails to load
const MFEUnavailable: React.FC<{ name?: string }> = ({ name }) => (
  <div style={{ 
    padding: '16px', 
    textAlign: 'center', 
    color: '#666',
    fontSize: '0.9em'
  }}>
    <p>{name || 'Micro Frontend'} is currently unavailable.</p>
    <p style={{ fontSize: '0.85em', marginTop: '8px', color: '#999' }}>
      Please ensure the MFE server is running.
    </p>
  </div>
);

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
      element.onerror = (event) => {
        // Silently handle script load errors - don't reject, resolve with null instead
        // This prevents React from logging the error
        resolve(null);
      }; 
    });

    document.head.appendChild(element); 
    promise.finally(() => document.head.removeChild(element)); 
    return promise; 
  }; 

  const loadModule = async (url: any, scope: any, module: any) => {
    try { 
      const container: any = await loadScope(url, scope); 
      
      // If container is null, script failed to load
      if (!container) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('MFE module not available:', url);
        }
        return { default: () => <MFEUnavailable name={props.data?.componentName || props.data?.name} /> };
      }
      
      await __webpack_init_sharing__('default'); 
      await container.init(__webpack_share_scopes__.default); 
      const factory = await container.get(module); 
      return factory(); 
    } catch (error) { 
      // Log error in development only
      if (process.env.NODE_ENV === 'development') {
        console.warn('MFE module not available:', url);
      }
      // Return a fallback component module instead of throwing
      return { default: () => <MFEUnavailable name={props.data?.componentName || props.data?.name} /> };
    } 
  }; 

  // Wrap the lazy import to handle errors gracefully
  const MFComp = React.lazy(() => {
    return loadModule( 
      props.data.componentURL || props.data.url, 
      props.data.componentName, 
      props.data.componentClass, 
    ).catch(() => {
      // Fallback if loadModule itself throws (shouldn't happen now, but just in case)
      return { default: () => <MFEUnavailable name={props.data?.componentName || props.data?.name} /> };
    });
  });

  // const setCustomerId = (id) => { 
  //   setCustomer({ customerId: id }); 
  // }; 

  return ( 
    <Suspense 
      fallback={ 
        <div className="parentDisable" > 
          <div className="spinner-border text-primary" role="status"> 
          </div> 
          <div className="loader mt-2 text-muted"></div> 
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