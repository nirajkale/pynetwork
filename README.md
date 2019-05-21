<h1> pynet </h1>
<h2>High performance socket swarms for network workloads</h2>
pynet package is designed to help write scripts/projects that rely on interprocess communication over a network.<br/>
Using pynet, this inter-network IPC can be achieved using minimal-to-no knowledge of sockets. Furthermore these data transfer/steaming
can be done in a swarm fashion, meaning multiple or swarm of persitant tcp connections that serve a single objective to deliver
high performance.<br/>
Following objectives can be achieved using this package:
<ul>
<li>Write subroutines/function that can stream data over to your client using callbacks (No need of polling)</li>
<li>Write subroutines/function that can send batches of data over to your client</li>
<li>Send data to your subroutines/function over network</li>
<li>Send files to & from server using swarm of connections for higher transfer rates</li>
</ul>
<br/>
Below are some use case tutorials using pynet:
