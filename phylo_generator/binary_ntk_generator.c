/* Copyright: Louxin Zhang
* Compiling command:  gcc binary_ntk_generator.c
* run command:  ./binary_ntk_generator <no. leaves> <no. reticulations> <no. of ntk generated>
* For example,  ./binary_ntk_generator 6 20 100
* Citation: Louxin Zhang, Zhang, L., 2016.
* On tree-based phylogenetic networks.
* Journal of Comput. Biology, 23(7), pp.553-565.
*  The study was supported by Merlion Project 2015
*/
/*
*  ------------------  method description ------------------------
*  The program is used to generate binary phylogenetic networks
*  over the given number of leaves with the given number of
*  reticulation nodes.
*  Given #(leaves) and #(ret. nodes), #(non-rooted tree nodes)
* can be computed. Then, define an array A of tree nodes,
* an array B of ret. nodes and an array C of leaves.
*
* The program simply keep on inserting an edge (u, v), where
* (1) u is randomly selected among all the nodes with
*  out-degree < 1 if u \in B,  <2 if u \in A or a root.
* (2) v is randomly selected among all the nodes with in-degree
*  < 2 if v\in B, <1 if v\in A and <0 if v\in C.
* The program stops until all the nodes satisfy the degree
* constraint.
*/

#include <stdio.h>
#include <time.h>
#include <stdlib.h>

/* return 0 if (src_node_array, target_node) is not a edge, 1 otherwise */
int Check(int source_node, int target_node, int Edges[][2], int no_edges) {
    int i;
	for (i = 0; i < no_edges; i++) {
		if (source_node == Edges[i][0] && target_node == Edges[i][1]) {
		    return 1;
		}
    }
	return 0;
}

/* argv[]: no._leaves, no._reticulations, no._data_sets */
int main(int argc, char * argv[])
{
    int  i, file_no, k, k_in, k_out;
    int n_r, n_t, n_l, internal_nodes;
    int nodes_type[300];
    int src_node_array[600];
    int tgt_node_array[600], source_node, target_node;
    int Edges[600][2], no_edges;
    int r, flag, count, success;
    char file_name[20];
    int good_candidate[600];
    int test;
    FILE * FPtr;
    int num_files;

    if (argc == 4) {
        n_l = atoi(argv[1]); /* num_leaves */
        n_r = atoi(argv[2]); /* num_reticulation */
        num_files = atoi(argv[3]);
    }
    else {
        fprintf(stderr, "usage: ./binary_ntk_generator <num_leaves> <num_reticulation> <num_networks>\n");
        exit(1);
    }

    n_t = n_r + n_l - 1; /* no of tree nodes */
    internal_nodes = n_t + n_r;   /* no of internal nodes */

    srand(time(NULL));
    for (file_no = 0; file_no < num_files; file_no++) {
        /* printf("the %d-th network\n", file_no); */
        do {
	        success = 1;
		    /* printf("do loop\n"); */
		    /* Set all nodes values as type value set to 1 */
            for (i = 0; i < internal_nodes + n_l; i++) {
                nodes_type[i] = 1;
            }

            /* randomly selected n_r nodes as reticulation nodes
               you will have n_r nodes have a value of node_type set to -1 */
            for (i = 0; i < n_r; i++) {
		        k = rand() % (internal_nodes - 2);
		        while (nodes_type[k + 2] == -1) {
		            k = rand() % (internal_nodes - 2);
		        }
                nodes_type[2 + k] = -1;
            }

            for (i = 0; i < internal_nodes; i++) {
                printf("%d ", nodes_type[i]);
            }
            printf("\n");

            k_in = 0;
            src_node_array[0] = 0;  /* two edges 0 and 1 are our edges from 0 */
            src_node_array[1] = 0; /* root has out links */
            k_out = 2;

            /* Create all possible edge candidates for the Network N. */
            for (i = 1; i < internal_nodes; i++) {
                if (nodes_type[i] == 1) {  /* tree nodes */
		            src_node_array[k_out] = i;
		            k_out = k_out + 1;
		            src_node_array[k_out] = i;
		            k_out += 1;
		            tgt_node_array[k_in] = i;
		            k_in += 1;
  	            }
  	            else { /* reticulation node */
	    	        src_node_array[k_out] = i;
	    	        k_out = k_out + 1;
	    	        tgt_node_array[k_in] = i;
	    	        k_in += 1;
	    	        tgt_node_array[k_in] = i;
	    	        k_in += 1;
                }
            }

            for (i = internal_nodes; i < internal_nodes + n_l; i++) {
                tgt_node_array[k_in] = i;
                k_in += 1;
            }

            printf("k_out %d  k_in %d\n", k_out, k_in);
            for (i = 0; i < k_out; i++) {
                printf("%d ", src_node_array[i]);
            }
            printf("\n");
            for (i = 0; i < k_in; i++) {
                printf("%d ", tgt_node_array[i]);
            }
            printf("\n");

            /* Create first edge leaving the root (node 0) to node 1 */
            no_edges = 0;
            Edges[0][0] = 0;
            Edges[0][1] = 1;
            no_edges += 1;

            /* printf("Edges\n %d  %d\n", 0, 1); */
            src_node_array[0] = -1;
            tgt_node_array[0] = -1;

            /* generate edges */
            for (i = 1; i < k_in; i++) {
                target_node = tgt_node_array[i];
	            flag = 0;
	            for (count = 0; count < k_out; count++) {
	                /* the format for all edges is that the source node number must be smaller than
	                   its destination node */
	     	        if (src_node_array[count] != -1 && src_node_array[count] < target_node) {
	     	            good_candidate[flag] = count;
	     	            flag += 1;
	     	        }
		            if (src_node_array[count] != -1 && src_node_array[count] > target_node) {
		                break;
		            }
	            }
	            /* failed, re-try building network as no valid edge candidates exist */
	            if (flag == 0) {
	                success = 0;
	                break;
	            }
	            /*
	            printf("in infinite look target_node=%d, flag=%d\n", target_node,  flag);
	            for (k=0; k<k_out; k++){  printf("%d ", src_node_array[k]);}
	            printf("\n");
	            */

	            test = 0;
                for ( ; ; ) {
		            test += 1;
		            if (test == 30) {
		                success = 0;
		                break;
		            }
	                r = rand() % flag;
		            /*
		            printf("r=%d   candidate=%d \n", r, src_node_array[good_candidate[r]]);
		            */
		            // If the node is not in Edges[][2], then create the entry and break out of loop!
   	                if (Check(src_node_array[good_candidate[r]], target_node, Edges, no_edges) == 0) {
		                source_node = src_node_array[good_candidate[r]];
		                src_node_array[good_candidate[r]] = -1;
		                /* printf("%d  %d\n", source_node, target_node); */
		                Edges[no_edges][0] = source_node;
		                Edges[no_edges][1] = target_node;
		                no_edges += 1;
		                break;
	                }
                }
	        /* printf("out infinite_loop=\n"); */
            } /* end for loop */
        } while (success == 0);
        /* printf("out success=\n"); */

        /* print */
        if (success == 1) {
            sprintf(file_name, "./0%d", file_no);
	        FPtr = fopen(file_name, "w+");
            if (FPtr != NULL) {
                for (i = 0; i < no_edges; i++) {
                    if (Edges[i][1] < internal_nodes) {
	                    fprintf(FPtr, "%d %d\n", Edges[i][0], Edges[i][1]);
		            }
		            else {
		                fprintf(FPtr, "%d leaf%d\n", Edges[i][0], Edges[i][1] - internal_nodes + 1);
		            }
                }
	            fclose(FPtr);
            }
        }
    } /* end of file_no loop */
}
