import React, { Suspense, useEffect, useRef } from 'react';


const DynamicComponent = (props: any) => { 
  
  // const [customer, setCustomer] = useState({ customerId }); 

  const loadScope = (url: any, scope: any) => {
    console.log(`[Dynamic] Loading scope "${scope}" from URL: ${url}`);

    // Check if already loaded
    if (window[scope] && window[scope].init && window[scope].get) {
      console.log(`[Dynamic] Scope "${scope}" already loaded`);
      return Promise.resolve(window[scope]);
    }

    // Check if script already exists
    const existingScript = document.querySelector(`script[src="${url}"]`);
    if (existingScript) {
      console.log(`[Dynamic] Script already exists, waiting for scope "${scope}"`);
      let retries = 0;
      const maxRetries = 100;
      return new Promise((resolve, reject) => {
        const checkContainer = () => {
          if (window[scope] && window[scope].init && window[scope].get) {
            console.log(`[Dynamic] Scope "${scope}" now available`);
            resolve(window[scope]);
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(checkContainer, 50);
          } else {
            reject(new Error(`Container for scope "${scope}" not found after waiting for existing script`));
          }
        };
        checkContainer();
      });
    }

    const element = document.createElement('script');

    const promise = new Promise((resolve, reject) => {

      element.src = url;

      element.type = 'text/javascript';

      element.async = true;

      element.onload = () => {
        console.log(`[Dynamic] Script loaded for scope "${scope}", waiting for container...`);
        // Wait a bit for the container to be available
        let retries = 0;
        const maxRetries = 100; // 5 seconds max
        const checkContainer = () => {
          if (window[scope] && window[scope].init && window[scope].get) {
            console.log(`[Dynamic] Container for scope "${scope}" is ready`);
            resolve(window[scope]);
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(checkContainer, 50);
          } else {
            console.error(`[Dynamic] Container for scope "${scope}" not found after ${maxRetries} retries`);
            reject(new Error(`Container for scope "${scope}" not found after loading script. Check: 1) MFE server is running on ${url}, 2) CORS headers are set, 3) Module Federation is configured correctly`));
          }
        };
        checkContainer();
      };

      element.onerror = (error) => {
        console.error(`[Dynamic] Failed to load script from ${url}:`, error);
        reject(new Error(`Failed to load script from ${url}. Check: 1) MFE server is running, 2) URL is correct, 3) CORS is enabled`));
      };

    });

    document.head.appendChild(element);
    console.log(`[Dynamic] Script element added to head for ${url}`);

    // Don't remove the script element - it needs to stay for Module Federation to work

    return promise;

  };

  const loadModule = async (url: any, scope: any, module: any) => {

    try {
      console.log(`[Dynamic] Loading module "${module}" from scope "${scope}"`);

      const container: any = await loadScope(url, scope);

      // Check if webpack sharing is available
      if (typeof __webpack_init_sharing__ === 'undefined') {
        console.warn('[Dynamic] __webpack_init_sharing__ is not available, attempting to initialize without sharing');
        // Try to initialize without sharing
        if (container.init) {
          await container.init({});
        }
      } else {
        console.log('[Dynamic] Initializing webpack sharing...');
        await __webpack_init_sharing__('default');
        
        if (typeof __webpack_share_scopes__ === 'undefined' || !__webpack_share_scopes__.default) {
          console.warn('[Dynamic] __webpack_share_scopes__ is not available, using empty object');
          await container.init({});
        } else {
          await container.init(__webpack_share_scopes__.default);
        }
      }

      console.log(`[Dynamic] Getting module "${module}" from container...`);
      const factory = await container.get(module);

      if (!factory) {
        throw new Error(`Module "${module}" not found in container. Available modules: ${Object.keys(container._remotes || {})}`);
      }

      console.log(`[Dynamic] Factory obtained, creating module...`);
      const moduleResult = factory();

      // Handle different module export formats
      // If it's already a component, return it wrapped
      // If it's a module object with default, extract default
      if (moduleResult && typeof moduleResult === 'object' && 'default' in moduleResult) {
        console.log('[Dynamic] Module has default export');
        return { default: moduleResult.default };
      }
      
      // If it's directly a component
      if (typeof moduleResult === 'function' || (typeof moduleResult === 'object' && moduleResult.$$typeof)) {
        console.log('[Dynamic] Module is a direct component');
        return { default: moduleResult };
      }

      // Fallback: return as-is
      console.log('[Dynamic] Returning module as-is');
      return { default: moduleResult };

    } catch (error) {

      console.error('[Dynamic] Error loading module:', error);
      console.error('[Dynamic] Error details:', {
        url,
        scope,
        module,
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined
      });

      throw error;

    }

  };

  

  const MFComp = React.lazy(() => {

    return loadModule( 

      props.data.componentURL || props.data.url,

      props.data.componentName,

      props.data.componentClass,

    );

  });

  // Debug: Track if component rendered
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (containerRef.current) {
      const childElements = containerRef.current.querySelectorAll('*');
      console.log(`[Dynamic] Component rendered. Found ${childElements.length} child elements in container`);
      if (childElements.length === 0) {
        console.warn('[Dynamic] Component container is empty - component may not be rendering content');
      }
    }
  }, []);

  

  // const setCustomerId = (id) => { 

  //   setCustomer({ customerId: id }); 

  // }; 

  

  return ( 

    <Suspense 

      fallback={
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <p>Loading {props.data.componentName || 'Micro Frontend'}...</p>
          <p style={{ fontSize: '0.9em', color: '#666' }}>
            Loading from {props.data.componentURL || props.data.url}
          </p>
        </div>
      } 

    > 
      <div 
        style={{ 
          border: '2px solid #4CAF50', 
          padding: '10px', 
          margin: '10px 0',
          backgroundColor: '#f0f8f0',
          minHeight: '100px',
          position: 'relative'
        }}
      >
        <p style={{ fontSize: '0.8em', color: '#666', margin: '0 0 10px 0', fontWeight: 'bold' }}>
          ✓ MFE Container - {props.data.componentName} (Component loaded successfully)
        </p>
        <div 
          ref={containerRef}
          style={{ border: '1px dashed #999', padding: '10px', minHeight: '50px' }}
        >
          {/* @ts-ignore - Remote component props are unknown */}
          <MFComp data={props.data} 
          currentUserToken={"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im01Qk42X0xMM3BVSzRUNVJDM1pPSSJ9.eyJhZHNJZCI6InR5bGVyLmxldW5nQHRlYW1oZ3MuY29tIiwidXNlckVtYWlsIjoidHlsZXIubGV1bmdAdGVhbWhncy5jb20iLCJhZ2VudElkIjoidHlsZXIubGV1bmdAdGVhbWhncy5jb20iLCJhZ2VudFJvbGVzIjpbInN1cGVydmlzb3IiLCJvcHNhZG1pbiIsInN1cGVydXNlciJdLCJkZXBhcnRtZW50IjoiU2FsZXMiLCJhcHBDbGllbnRJZCI6IkFnZW50eCIsIm5pY2tuYW1lIjoidHlsZXIubGV1bmciLCJuYW1lIjoidHlsZXIubGV1bmdAdGVhbWhncy5jb20iLCJwaWN0dXJlIjoiaHR0cHM6Ly9zLmdyYXZhdGFyLmNvbS9hdmF0YXIvNjk5NDdhNTRiNGIxZjQwZDk5MDMwYjIwMTE0YTc3YzM_cz00ODAmcj1wZyZkPWh0dHBzJTNBJTJGJTJGY2RuLmF1dGgwLmNvbSUyRmF2YXRhcnMlMkZ0eS5wbmciLCJ1cGRhdGVkX2F0IjoiMjAyNS0xMi0zMVQxNzoyMTo1My44MzRaIiwiZW1haWwiOiJ0eWxlci5sZXVuZ0B0ZWFtaGdzLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6Ly9hZ2VudHgtZGV2LXNhbXBsZS51cy5hdXRoMC5jb20vIiwiYXVkIjoiNzFjN1lEYUxGa21TZUViR2F3bTlWZ25JZnRIVnEzNjQiLCJzdWIiOiJhdXRoMHw2OGNkYWNlNDlkYjFlZmExYTEzYjA3ODEiLCJpYXQiOjE3NjcyMDE3MjEsImV4cCI6MTc2NzIzNzcxOSwic2lkIjoieG55SXNKajRaR0hSSk5fN3hFanprdDNIc0oxMW03cmwiLCJub25jZSI6ImQzNTBOazh4TTFoNmRYaHpiR3BZYkdZeVVrbCtZa0l3UVd4MGRURXpOREoxU2xJMGVrNUVNV3N3ZFE9PSIsIm9yZ19pZCI6Im9yZ19iS01YTnBoRzg0Wm5GZUtmIn0.YLyz9pxtmv8mecyKMyxSbRHvDTae6MRyFmnTBe_ki9iOX8-g2oKMCWxxLEk6HgIb1AWFKA6HfKwzQLpXIJe0wmgWThwJ0xd-rwckTk2rP_9ixSS92b3o3pyY_VO1O93R2PY0h3U7ryR4m_AfJ2VhjDav6eABTvy4REFb970Bp4uVLrc4yCKdv7VflmzD_ekc3dEqpy8aMhbOZGe4WCw4x1YQALYECDDX4c89LKfNOh9J6453mURM-0gH7y7qGPXaa1x04OME9ZO9GEoo30BS1xZeLoMYkRFhEd6qMrFViAU9vwcSi7-EFwgDXNeCXJopwcWPXgfknJpj5ACXvUVbPw"} /> 
        </div>
        {/* Debug: If you see this but not the component above, the component is rendering but might be hidden or waiting for Auth0/config */}
      </div>
        {/* {props.data.componentName} */} 


    </Suspense> 

  ); 

}; 

  

export default DynamicComponent; 