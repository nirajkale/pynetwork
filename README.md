  # pynet
  ##  High performance socket swarms for network workloads
  
  ### Prelude
 
  As a fun project, i wanted a raspberry pi based RC car that can be controlled over wi-fi. On the receiver end, a combination of  different deep neural network architectures that can consume the data from raspberry pi like camera feed ( to a CNN model), feed from various sensors e.g proximity, speed encoder etc ( to a RNN) & then can subsequently control it.
  But one of the fundamental problems that i faced while implementing it was how to transfer all of this data back & forth between my laptop & pi in real time with low latency.
  This gave me an idea write a simple JSON based networking code that could transfer custom python objects back & forth, but that was enough because i was dealing multiple data feeds & manging these multiple tcp connections was getting difficult & hence i decided to buckle up and write down a networking library that could manage swarm of connections & also could help stream the data from python subroutines (These subroutines were pythonian generators that could endlessly read & stream the individual sensor data). Apart from subroutines based streaming, I also wanted to add batch fashioned suboutine data transfer (As you may have realized lot of these ideas sound similar to Keras generators that are used for feeding data to a machine learning model) 

  pynet package is designed to help write scripts/projects that rely on interprocess communication over a network. Using pynet, this 
  inter-network IPC can be achieved using minimal-to-no knowledge of sockets. Furthermore these data transfer/steaming can be done in 
  a swarm fashion, meaning multiple or swarm of persitant tcp connections that serve a single objective to deliver high performance.
  Following objectives can be achieved using this package:

  1. Write subroutines/function that can stream data over to your client using callbacks (No need of polling)
  2. Write subroutines/function that can send batches of data over to your client
  3. Send data to your subroutines/function over network
  4. Send files to & from server using swarm of connections for higher transfer rates

  Before jumping on to some use cases, below is some nomenclatures & components that you should be aware before using it:
  There are 4 main components involved namely: Gateway, Controller, Handler & a Client. Gateway acts as a small server which listens
  to requests made by Controller on a specified port. Gateway & Controller share a Many-to-Many relationship (One Gateway can respond
  to multiple Controllers & one Controller can connect to multiple Gateways). Gateway-controller themselves do perform any workload
  operation (like data/file transfer) but instead they are responsible spawning & managing a swarm\s of tcp connections to handle 
  your workloads. </p><p>Whenever a controller requests to a Gateway, Gateway spawns a Handler & sends an acknowledge to the Controller
  then Controller creates a Client for that Handler. So 1 request results in spawning of a pair of "Handler <-> Client". A handler &
  a client work in tandem to handle your custom workload. To improve speed of your operation, you can spawn multiple pairs of Handler
  & client. Each handler spwned at the Gateway runs on a independent python-thread (this where the performance boost comes from)These       handler are managed by Gateway. The number of possible Handlers<->Clients that can be spawned depends the size of Handler 
  pool (Basically a custom thread pool). By default the pool size is 5 but you can increase it any number depending on your hardware.
  
  **The swarm architecture looks something like this**
  <img src="https://user-images.githubusercontent.com/40765055/58163266-53432900-7ca1-11e9-8c94-928eb364faf7.jpg" /></p>


Below are some of the use case tutorials using pynet with increasing complexity:
<br/>
<h2> Conditional File Backup </h2>
<info>
  Consider a scenario where you have a limited storage on a VM node or a server and would like to to move older files from this device
  to your local machine when the storage usage crosses 75%, also you want to move just enough files to reduce usage to 25% (starting from 
  the older files). This objective 
</info>
