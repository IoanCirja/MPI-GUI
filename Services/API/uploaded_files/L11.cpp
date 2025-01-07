#include <stdio.h>
#include "mpi.h"
#include <stdlib.h>

#define NEW_ID 0
#define CHEF 1

int main (int argc, char ** argv) {

    MPI_Init( &argc , &argv);

    MPI_Status status;

    int rank, count;
    MPI_Comm_rank( MPI_COMM_WORLD , &rank);
    MPI_Comm_size( MPI_COMM_WORLD , &count);

    int v[] = {8, 2, 6, 4, 7, 3, 5, 1};
    int new_id = v[rank];

    int lider = rank, leader_id = new_id;

    int registru[2];

    bool should_continue = true;
    bool asleep = true;
    bool state = false;


    while (should_continue) {     
        if (asleep) {
            int send[] = { new_id, rank };
            MPI_Send( &send , 2 , MPI_INT , (rank + 1) % count , NEW_ID , MPI_COMM_WORLD);
            asleep = false;
        }
        else {
            MPI_Recv( &registru , 2 , MPI_INT , (rank == 0) ? count - 1 : rank - 1 , MPI_ANY_TAG , MPI_COMM_WORLD , &status);

            switch (status.MPI_TAG) {
                case NEW_ID:
                    if (registru[0] == new_id) {
                        lider = registru[1];
                        leader_id = registru[0];
                        int send[] = { new_id, lider };
                        MPI_Send( &send , 2 , MPI_INT , (rank + 1) % count , CHEF , MPI_COMM_WORLD);
                        should_continue = false;
                        state = true;
                    }
                    if (registru[0] > new_id) {
                        MPI_Send( &registru , 2 , MPI_INT , (rank + 1) % count , NEW_ID , MPI_COMM_WORLD);
                    }
                    break;
                case CHEF:
                    state = false;
                    lider = registru[1];
                    leader_id = registru[0];
                    MPI_Send( &registru , 2 , MPI_INT , (rank + 1) % count , CHEF , MPI_COMM_WORLD);
                    should_continue = false;
                    break;
                default:
                    break;
            }
        }

    }



    if(rank != lider)
        printf("Procesul %d(%d) a gasit chef pe procesul %d(%d)\n", rank, new_id, leader_id, lider);

    MPI_Finalize();

    return 0;
}