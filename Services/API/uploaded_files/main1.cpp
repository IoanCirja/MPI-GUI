#include <stdlib.h>
#include "mpi.h"

int main(int argc, char ** argv)
{
    MPI_Init(&argc, &argv);

    /*
        0 -> 4
        1 -> 6
        2 -> 4, 7, 8
        3 -> 4, 6
        4 -> 4, 2, 3, 0
        5 -> 6
        6 -> 3, 1, 5
        7 -> 2
        8 -> 2
    */

    MPI_Comm tree_com;
    int nnodes = 9;
    int edges[] = { 4,
                    6,
                    4, 7, 8,
                    4, 6,
                    4, 2, 3, 0,
                    6,
                    3, 1, 5,
                    2, 
                    2 };

    int index[9] = {1, 2, 5, 7, 11, 12, 15, 16, 17};


    MPI_Graph_create(MPI_COMM_WORLD, nnodes, index, edges, 0, &tree_com);
    int rank;
    MPI_Comm_rank(tree_com, &rank);

    int nvecini;
    MPI_Graph_neighbors_count(tree_com, rank, &nvecini);

    int vecini[nvecini];
    MPI_Graph_neighbors(tree_com, rank, nvecini, vecini);

    int sum = 0;
    int recv;
    
    MPI_Status status;

    if(rank == vecini[0])//radacina
    {
        //primeste de la vecinii[1..nvecini]
        for(int i = 1; i < nvecini; ++i)
        {
            MPI_Recv(&recv, 1, MPI_INT, vecini[i], 100, tree_com, &status);
            sum += recv;
        }
        printf("Suma in nodul %d este: %d\n", rank, sum);

    }
    else if(nvecini == 1)//frunze
    {
        //primeste de la vecini[0]
        MPI_Send(&rank, 1, MPI_INT, vecini[0], 100, tree_com);
    }
    else//noduri
    {
         for(int i = 1; i < nvecini; ++i)
        {
            MPI_Recv(&recv, 1, MPI_INT, vecini[i], 100, tree_com, &status);
            sum += recv;
        }
        printf("Suma in nodul %d este: %d\n", rank, sum);

        MPI_Send(&sum, 1, MPI_INT, vecini[0], 100, tree_com);
    }
    
    MPI_Finalize();

    return 0;
}