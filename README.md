#pynet
##High performance socket swarms for network workloads

pynet package is designed to help write scripts/projects that rely on interprocess communication over a network.<br/>
Using pynet, this inter-network IPC can be achieved using minimal-to-no knowledge of sockets. Furthermore these data transfer/steaming
can be done in a swarm fashion, meaning multiple or swarm of persitant tcp connections that serve a single objective to deliver
high performance.<br/>
Following objectives can be achieved using this package:

..* Write subroutines/function that can stream data over to your client using callbacks (No need of polling)</li>
..* Write subroutines/function that can send batches of data over to your client</li>
..* Send data to your subroutines/function over network</li>
..* Send files to & from server using swarm of connections for higher transfer rates</li>

  Before jumping on to some use cases, below is some nomenclatures & components that you should be aware before using it:
  There are 4 main components involved namely: Gateway, Controller, Handler & a Client. Gateway acts as a small server which listens
  to requests made by Controller on a specified port. Gateway & Controller share a Many-to-Many relationship (One Gateway can respond
  to multiple Controllers & one Controller can connect to multiple Gateways). Gateway-controller themselves do perform any workload
  operation (like data/file transfer) but instead they are responsible spawning & managing a swarm\s of tcp connections to handle 
  your workloads. </p><p>Whenever a controller requests to a Gateway, Gateway spawns a Handler & sends an acknowledge to the Controller
  then Controller creates a Client for that Handler. So 1 request results in spawning of a pair of "Handler <-> Client". A handler &
  a client work in tandem to handle your custom workload. To improve speed of your operation, you can spawn multiple pairs of Handler
  & client. Each handler spwned at the Gateway runs on a independent python-thread (this where the performance boost comes from)These     handler are managed by Gateway. The number of possible Handlers<->Clients that can be spawned depends the size of Handler 
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
