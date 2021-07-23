/* Copyright: Louxin Zhang
* Compiling command:  gcc binary_ntk_generator.c
* run command:  ./a.out <no. leaves> <no. reticulations> <no. of ntk generated>
* For example,  ./a.out 6 20 100
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

/* return 0 if (out_copy, node2) is not a edge, 1 otherwise */
int  Check(int node1, int node2, int Edges[][2], int no_edges) {
    int i;
	for (i = 0; i < no_edges; i++) {
		if (node1 == Edges[i][0] && node2 == Edges[i][1]) {
		    return 1;
		}
    }
	return 0;
}

/* argv[]: no._leaves, no._reticulations, no._data_sets */
int main(int argc, char *argv[])
{
    int  i, j, k, k_in, k_out;
    int n_r, n_t, n_l, n;
    int nodes[300], nodes_type[300];
    int out_copy[600];
    int in_copy[600], node1, node2;
    int Edges[600][2], no_edges;
    int r, flag, count, file_series, success;
    char file_name[20];
    int good_candidate[600];
    int test;
    FILE * FPtr;
    int m;
    int num_files;

    if (argc >=4) {
        n_l = atoi(argv[1]); /* num_leaves */
        n_r = atoi(argv[2]); /* num_reticulation */
        num_files = atoi(argv[3]);
    }

    n_t = n_r + n_l - 1; /* no of tree nodes */
    n = n_t + n_r;   /* no of internal nodes */

    srand(time(NULL));
    file_series = 0;
    for (j = 0; j < num_files; j++) {
        /* printf("the %d-th network\n", j); */
        do {
	        success = 1;
		    /* printf("do loop\n"); */
            for (i = 0; i < n+n_l; i++) {
                nodes_type[i]=1;
            }

            /* randomly selected n_r nodes as reticulation nodes */
            for (i = 0; i < n_r; i++) {
		        k = rand() % (n-2);
		        while (nodes_type[k + 2] == -1) {
		            k=rand() % (n - 2);
		        }
                nodes_type[2+k]=-1;
            }

            for (i=0; i < n; i++) {
                printf("%d ", nodes_type[i]);
            }
            printf("\n");

            k_in = 0;
            out_copy[0] = 0;  /* two edges 0 and 1 are our edges from 0 */
            out_copy[1] = 0; /* root has out links */
            k_out=2;

            for (i = 1; i < n; i++) {
                if (nodes_type[i] == 1) {  /* tree nodes */
		            out_copy[k_out] = i;
		            k_out=k_out+1;
		            out_copy[k_out] = i;
		            k_out +=1;
		            in_copy[k_in] = i;
		            k_in += 1;
  	            }
  	            else { /* reticulation node */
	    	        out_copy[k_out] = i;
	    	        k_out=k_out+1;
	    	        in_copy[k_in] = i;
	    	        k_in += 1;
	    	        in_copy[k_in] = i;
	    	        k_in +=1;
                }
            }

            for (i = n; i < n + n_l; i++) {
                in_copy[k_in] = i;
                k_in += 1;
            }

            printf("k_out %d  k_in %d\n", k_out, k_in);
            for (i=0; i<k_out; i++) {
                printf("%d ", out_copy[i]);
            }
            printf("\n");
            for (i=0; i<k_in; i++) {
                printf("%d ", in_copy[i]);
            }
            printf("\n");

            no_edges = 0;
            Edges[0][0] = 0;
            Edges[0][1] = 1;
            no_edges += 1;

            /* printf("Edges\n %d  %d\n", 0, 1); */
            out_copy[0] = -1;
            in_copy[0] = -1;

            /* generate edges */
            for (i=1; i<k_in; i++) {
                node2 = in_copy[i];
	            flag = 0;
	            for (count=0; count<k_out; count++) {
	     	        if (out_copy[count] !=-1 && out_copy[count]< node2) {
	     	            good_candidate[flag]=count; flag +=1;
	     	        }
		            if (out_copy[count] !=-1 && out_copy[count]> node2) {
		                break;
		            }
	            }
	            if (flag == 0) {
	                success=0;
	                break;
	            }
	            /*
	            printf("in infinite look node2=%d, flag=%d\n", node2,  flag);
	            for (k=0; k<k_out; k++){  printf("%d ", out_copy[k]);}
	            printf("\n");
	            */

	            test = 0;
                for ( ; ; ) {
		            test += 1;
		            if (test == 30) {
		                success=0;
		                break;
		            }
	                r = rand() % flag;
		            /*
		            printf("r=%d   candidate=%d \n", r, out_copy[good_candidate[r]]);
		            */
   	                if (Check(out_copy[good_candidate[r]], node2, Edges, no_edges)==0) {
		                node1 = out_copy[good_candidate[r]];
		                out_copy[good_candidate[r]] = -1;
		                /* printf("%d  %d\n", node1, node2); */
		                Edges[no_edges][0] = node1;
		                Edges[no_edges][1] = node2;
		                no_edges += 1;
		                break;
	                }
                }
	        /* printf("out infinite_loop=\n"); */
            } /* end for loop */
        } while (success==0);
        /* printf("out success=\n"); */

        /* print */
        if (success ==1) {
            sprintf(file_name, "./0%d.txt", j);
	        FPtr = fopen(file_name, "w");
            if (FPtr != NULL) {
                for (i = 0; i < no_edges; i++) {
                    if (Edges[i][1] < n) {
	                    fprintf(FPtr, "%d %d\n", Edges[i][0], Edges[i][1]);
		            }
		            else {
		                fprintf(FPtr, "%d leaf%d\n", Edges[i][0], Edges[i][1] - n + 1);
		            }
                }
	            fclose(FPtr);
            }
        }
    } /* end of j loop */
}
